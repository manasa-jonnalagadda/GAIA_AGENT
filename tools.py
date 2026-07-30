import os
import base64
import pandas as pd
from pypdf import PdfReader
from PIL import Image
from smolagents import Tool
import litellm

class FileReaderTool(Tool):
    name = "file_reader"
    description = (
        "Reads local files (csv, xlsx, txt, images, pdf) given a file path, "
        "and returns extracted text or a description. Dispatch logic by file extension."
    )
    inputs = {
        "file_path": {
            "type": "string",
            "description": "The absolute or relative path to the local file to read."
        }
    }
    output_type = "string"

    def __init__(self, model_id=None, api_key=None, **kwargs):
        super().__init__(**kwargs)
        self.model_id = model_id
        self.api_key = api_key

    def forward(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
                if len(df) <= 200:
                    return df.to_string()
                else:
                    return (
                        f"CSV shape: {df.shape}. Columns: {df.columns.tolist()}.\n"
                        f"First 5 rows:\n{df.head(5).to_string()}\n"
                        f"Last 5 rows:\n{df.tail(5).to_string()}"
                    )
                    
            elif ext in [".xlsx", ".xls"]:
                xls = pd.ExcelFile(file_path)
                sheets = xls.sheet_names
                result = [f"Excel file sheets: {sheets}"]
                for sheet in sheets:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    result.append(f"Sheet '{sheet}' shape: {df.shape}")
                    if len(df) <= 200:
                        result.append(df.to_string())
                    else:
                        result.append(
                            f"First 5 rows:\n{df.head(5).to_string()}\n"
                            f"Last 5 rows:\n{df.tail(5).to_string()}"
                        )
                return "\n\n".join(result)
                
            elif ext == ".pdf":
                reader = PdfReader(file_path)
                text = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text.append(f"--- Page {i+1} ---")
                    text.append(page_text)
                
                full_text = "\n".join(text)
                if len(full_text) > 8000:
                    note = f"\n\n[NOTE: PDF text has been truncated from {len(full_text)} to 8000 characters to prevent context window overflow.]"
                    return full_text[:8000] + note
                return full_text
                
            elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
                # Read image metadata first
                img_metadata = ""
                try:
                    with Image.open(file_path) as img:
                        img_metadata = f"Image format: {img.format}, Size: {img.size}, Mode: {img.mode}"
                except Exception as e:
                    img_metadata = f"Could not read image metadata: {e}"
                
                api_key = self.api_key or os.environ.get("LLM_API_KEY")
                model_id = self.model_id or os.environ.get("LLM_MODEL_ID", "gpt-4o")
                
                if not api_key:
                    return f"Image read fallback ({img_metadata}) - LLM_API_KEY is not set for image description."
                
                try:
                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    mime_type = "image/png"
                    if ext in [".jpg", ".jpeg"]:
                        mime_type = "image/jpeg"
                    elif ext == ".webp":
                        mime_type = "image/webp"
                        
                    response = litellm.completion(
                        model=model_id,
                        api_key=api_key,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Describe this image in detail and transcribe any text you see in it."},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{encoded_string}"
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                    desc = response.choices[0].message.content
                    return f"Image metadata: {img_metadata}\n\nImage description and transcription:\n{desc}"
                except Exception as e:
                    return f"Failed to describe image via multimodal LLM: {e}. Image metadata: {img_metadata}"
                    
            else:
                # Text files or fallback
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="latin-1") as f:
                        return f.read()
                        
        except Exception as e:
            return f"Error reading file '{file_path}': {e}"
