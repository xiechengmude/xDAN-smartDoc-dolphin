"""
Asynchronous Dolphin engine for high-performance document processing.
"""

import asyncio
import gc
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import torch
from PIL import Image
from transformers import AutoProcessor, VisionEncoderDecoderModel

from ..core.config import settings
from ..core.logging import model_logger
from ..core.models import DocumentElement, ElementType
from ..utils.image_utils import prepare_image, process_coordinates
from ..utils.parsing_utils import parse_layout_string


class AsyncDolphinEngine:
    """
    Asynchronous Dolphin engine for high-performance document processing.
    
    Features:
    - Asynchronous processing with proper concurrency control
    - GPU memory management and optimization
    - Batch processing for improved throughput
    - Model warm-up and caching
    - Error handling and recovery
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the async Dolphin engine."""
        self.model_path = model_path or settings.model_path
        self.device = settings.model_device
        self.max_batch_size = settings.max_batch_size
        self.precision = settings.model_precision
        
        # Model components
        self.processor: Optional[AutoProcessor] = None
        self.model: Optional[VisionEncoderDecoderModel] = None
        self.tokenizer = None
        
        # Performance tracking
        self._model_loaded = False
        self._warm_up_done = False
        self._processing_lock = asyncio.Semaphore(settings.max_concurrent_tasks)
        
        model_logger.info("AsyncDolphinEngine initialized", 
                         model_path=self.model_path, 
                         device=self.device)
    
    async def load_model(self) -> None:
        """Load the Dolphin model asynchronously."""
        if self._model_loaded:
            return
            
        model_logger.info("Loading Dolphin model", path=self.model_path)
        start_time = time.time()
        
        try:
            # Load in separate thread to avoid blocking event loop
            await asyncio.get_event_loop().run_in_executor(
                None, self._load_model_sync
            )
            
            load_time = time.time() - start_time
            model_logger.info("Model loaded successfully", 
                             load_time=f"{load_time:.2f}s",
                             device=self.device)
            
            # Warm up the model
            await self._warm_up_model()
            
        except Exception as e:
            model_logger.error("Failed to load model", error=str(e))
            raise
    
    def _load_model_sync(self) -> None:
        """Synchronous model loading."""
        # Load processor and model
        self.processor = AutoProcessor.from_pretrained(self.model_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.model_path)
        
        # Set device and precision
        self.model.to(self.device)
        if self.precision == "half" and self.device != "cpu":
            self.model = self.model.half()
        
        self.model.eval()
        self.tokenizer = self.processor.tokenizer
        self._model_loaded = True
    
    async def _warm_up_model(self) -> None:
        """Warm up the model with dummy data."""
        if self._warm_up_done:
            return
            
        model_logger.info("Warming up model")
        
        try:
            # Create dummy image and prompt
            dummy_image = Image.new('RGB', (1024, 1024), color='white')
            dummy_prompt = "Parse the reading order of this document."
            
            # Run warm-up inference
            await self.chat(dummy_prompt, dummy_image)
            
            self._warm_up_done = True
            model_logger.info("Model warm-up completed")
            
        except Exception as e:
            model_logger.warning("Model warm-up failed", error=str(e))
    
    async def chat(
        self, 
        prompt: Union[str, List[str]], 
        image: Union[Image.Image, List[Image.Image]]
    ) -> Union[str, List[str]]:
        """
        Process image(s) with prompt(s) asynchronously.
        
        Args:
            prompt: Text prompt or list of prompts
            image: PIL Image or list of PIL Images
            
        Returns:
            Generated text or list of texts
        """
        if not self._model_loaded:
            await self.load_model()
        
        async with self._processing_lock:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._chat_sync, prompt, image
            )
    
    def _chat_sync(
        self, 
        prompt: Union[str, List[str]], 
        image: Union[Image.Image, List[Image.Image]]
    ) -> Union[str, List[str]]:
        """Synchronous chat processing."""
        # Check if we're dealing with a batch
        is_batch = isinstance(image, list)
        
        if not is_batch:
            images = [image]
            prompts = [prompt]
        else:
            images = image
            prompts = prompt if isinstance(prompt, list) else [prompt] * len(images)
        
        try:
            # Prepare images
            batch_inputs = self.processor(images, return_tensors="pt", padding=True)
            batch_pixel_values = batch_inputs.pixel_values
            
            if self.precision == "half" and self.device != "cpu":
                batch_pixel_values = batch_pixel_values.half()
            
            batch_pixel_values = batch_pixel_values.to(self.device)
            
            # Prepare prompts
            prompts = [f"<s>{p} <Answer/>" for p in prompts]
            batch_prompt_inputs = self.tokenizer(
                prompts,
                add_special_tokens=False,
                return_tensors="pt",
                padding=True
            )
            
            batch_prompt_ids = batch_prompt_inputs.input_ids.to(self.device)
            batch_attention_mask = batch_prompt_inputs.attention_mask.to(self.device)
            
            # Generate text
            with torch.inference_mode():
                outputs = self.model.generate(
                    pixel_values=batch_pixel_values,
                    decoder_input_ids=batch_prompt_ids,
                    decoder_attention_mask=batch_attention_mask,
                    min_length=1,
                    max_length=settings.max_sequence_length,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,
                    bad_words_ids=[[self.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                    do_sample=False,
                    num_beams=1,
                    repetition_penalty=1.1
                )
            
            # Decode results
            sequences = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)
            
            # Clean output
            results = []
            for i, sequence in enumerate(sequences):
                cleaned = sequence.replace(prompts[i], "").replace("<pad>", "").replace("</s>", "").strip()
                results.append(cleaned)
            
            # Return single result for single image input
            if not is_batch:
                return results[0]
            return results
            
        except Exception as e:
            model_logger.error("Chat processing failed", error=str(e))
            raise
        finally:
            # Clean up GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    async def process_page(
        self, 
        image: Image.Image, 
        max_batch_size: Optional[int] = None
    ) -> Tuple[List[DocumentElement], float]:
        """
        Process a document page asynchronously.
        
        Args:
            image: Document page image
            max_batch_size: Maximum batch size for element processing
            
        Returns:
            Tuple of (document elements, processing time)
        """
        start_time = time.time()
        
        try:
            # Stage 1: Page-level layout and reading order parsing
            layout_output = await self.chat("Parse the reading order of this document.", image)
            
            # Stage 2: Element-level content parsing
            padded_image, dims = await asyncio.get_event_loop().run_in_executor(
                None, prepare_image, image
            )
            
            elements = await self._process_elements(
                layout_output, padded_image, dims, max_batch_size
            )
            
            processing_time = time.time() - start_time
            
            model_logger.info("Page processing completed",
                             elements_count=len(elements),
                             processing_time=f"{processing_time:.2f}s")
            
            return elements, processing_time
            
        except Exception as e:
            model_logger.error("Page processing failed", error=str(e))
            raise
    
    async def _process_elements(
        self,
        layout_results: str,
        padded_image: Any,
        dims: Tuple[int, int],
        max_batch_size: Optional[int] = None
    ) -> List[DocumentElement]:
        """Process document elements with parallel decoding."""
        max_batch_size = max_batch_size or self.max_batch_size
        
        # Parse layout results
        layout_data = await asyncio.get_event_loop().run_in_executor(
            None, parse_layout_string, layout_results
        )
        
        # Group elements by type
        text_elements = []
        table_elements = []
        figure_elements = []
        
        previous_box = None
        reading_order = 0
        
        for bbox, label in layout_data:
            try:
                # Process coordinates
                coords_result = await asyncio.get_event_loop().run_in_executor(
                    None, process_coordinates, bbox, padded_image, dims, previous_box
                )
                x1, y1, x2, y2, orig_x1, orig_y1, orig_x2, orig_y2, previous_box = coords_result
                
                # Crop element
                cropped = padded_image[y1:y2, x1:x2]
                if cropped.size > 0:
                    if label == "fig":
                        # Figure elements don't need text extraction
                        figure_elements.append(DocumentElement(
                            element_type=ElementType.FIGURE,
                            bbox=[orig_x1, orig_y1, orig_x2, orig_y2],
                            text="",
                            reading_order=reading_order
                        ))
                    else:
                        # Prepare for text extraction
                        pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                        element_info = {
                            "crop": pil_crop,
                            "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                            "reading_order": reading_order,
                        }
                        
                        if label == "tab":
                            table_elements.append(element_info)
                        else:
                            text_elements.append(element_info)
                
                reading_order += 1
                
            except Exception as e:
                model_logger.warning("Failed to process element", 
                                   label=label, error=str(e))
                continue
        
        # Process elements in parallel
        all_elements = figure_elements.copy()
        
        # Process text elements
        if text_elements:
            text_results = await self._process_element_batch(
                text_elements, "Read text in the image.", max_batch_size
            )
            all_elements.extend(text_results)
        
        # Process table elements
        if table_elements:
            table_results = await self._process_element_batch(
                table_elements, "Parse the table in the image.", max_batch_size
            )
            all_elements.extend(table_results)
        
        # Sort by reading order
        all_elements.sort(key=lambda x: x.reading_order)
        
        return all_elements
    
    async def _process_element_batch(
        self,
        elements: List[Dict[str, Any]],
        prompt: str,
        max_batch_size: int
    ) -> List[DocumentElement]:
        """Process elements of the same type in batches."""
        results = []
        
        # Process in batches
        for i in range(0, len(elements), max_batch_size):
            batch = elements[i:i + max_batch_size]
            crops = [elem["crop"] for elem in batch]
            prompts = [prompt] * len(crops)
            
            try:
                # Process batch
                texts = await self.chat(prompts, crops)
                
                # Create document elements
                for j, (elem, text) in enumerate(zip(batch, texts)):
                    element_type = ElementType.TABLE if "table" in prompt.lower() else ElementType.TEXT
                    
                    doc_element = DocumentElement(
                        element_type=element_type,
                        bbox=elem["bbox"],
                        text=text,
                        reading_order=elem["reading_order"]
                    )
                    results.append(doc_element)
                    
            except Exception as e:
                model_logger.error("Batch processing failed", 
                                 batch_size=len(batch), error=str(e))
                # Add empty elements for failed batch
                for elem in batch:
                    doc_element = DocumentElement(
                        element_type=ElementType.TEXT,
                        bbox=elem["bbox"],
                        text="",
                        reading_order=elem["reading_order"]
                    )
                    results.append(doc_element)
        
        return results
    
    async def unload_model(self) -> None:
        """Unload the model to free memory."""
        if not self._model_loaded:
            return
        
        model_logger.info("Unloading model")
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._unload_model_sync
            )
            model_logger.info("Model unloaded successfully")
        except Exception as e:
            model_logger.error("Failed to unload model", error=str(e))
    
    def _unload_model_sync(self) -> None:
        """Synchronous model unloading."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        self.tokenizer = None
        self._model_loaded = False
        self._warm_up_done = False
        
        # Clean up GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
    
    def __del__(self):
        """Cleanup when engine is destroyed."""
        if self._model_loaded:
            try:
                self._unload_model_sync()
            except Exception:
                pass 