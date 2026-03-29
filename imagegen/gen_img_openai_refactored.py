"""
Image Generation Module - Path-Agnostic Version
Generates images using OpenAI DALL-E 3 API
All paths are passed as parameters - no hardcoded paths
"""
import json
import os
import time
import requests
import openai
from pathlib import Path
from typing import Optional


def download_image(url: str, file_path: Path) -> bool:
    """
    Download an image from a URL and save it to the specified file path.
    
    Args:
        url: Image URL to download
        file_path: Path where image should be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Saved: {file_path}")
            return True
        else:
            print(f"Failed to download image from {url}: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False


def generate_openai_image(
    prompt: str,
    api_key: str,
    num_images: int = 1,
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard"
) -> list:
    """
    Generate images using OpenAI DALL-E API.
    
    Args:
        prompt: Text prompt for image generation
        api_key: OpenAI API key
        num_images: Number of images to generate (default: 1)
        model: DALL-E model to use (default: dall-e-3)
        size: Image size (default: 1024x1024)
        quality: Image quality (default: standard)
        
    Returns:
        List of image URLs
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        
        enhanced_prompt = f"High quality realistic image: {prompt}. Professional photography, detailed, clear focus."
        
        response = client.images.generate(
            model=model,
            prompt=enhanced_prompt,
            size=size,
            quality=quality,
            n=num_images,
        )
        
        image_urls = [data.url for data in response.data]
        return image_urls
        
    except Exception as e:
        print(f"OpenAI DALL-E API request failed: {e}")
        return []


def main_generate_images(
    script_path: Path,
    images_output_path: Path,
    api_key: str,
    delay_seconds: float = 2.0
) -> bool:
    """
    Main function to process the JSON and generate/download images using OpenAI DALL-E.
    
    Args:
        script_path: Path to the script JSON file
        images_output_path: Directory where images should be saved
        api_key: OpenAI API key
        delay_seconds: Delay between API calls to avoid rate limits
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure paths are Path objects
    script_path = Path(script_path)
    images_output_path = Path(images_output_path)
    
    # Ensure output directory exists
    images_output_path.mkdir(parents=True, exist_ok=True)
    
    # Load and parse JSON
    try:
        with open(script_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        return False
    except FileNotFoundError:
        print(f"Script file not found: {script_path}")
        return False

    # Validate JSON structure
    if "visual_script" not in data:
        print("Missing key 'visual_script' in JSON.")
        return False

    # Process each scene
    success_count = 0
    for idx, scene in enumerate(data["visual_script"]):
        try:
            prompt = scene.get("prompt")
            if not prompt:
                print(f"Scene {idx}: Missing prompt, skipping")
                continue
            
            timestamp = scene.get("timestamp_start", f"{idx:03d}")
            scene_id = timestamp.replace(":", "-")

            # Generate images using OpenAI DALL-E
            print(f"Generating image for prompt: {prompt}")
            image_urls = generate_openai_image(prompt, api_key, num_images=1)
            
            if not image_urls:
                print(f"No images generated for prompt: {prompt}")
                continue

            # Use the first generated image
            image_url = image_urls[0]
            if not image_url:
                print(f"No suitable image generated for prompt: {prompt}")
                continue

            # Download the generated image
            file_path = images_output_path / f"scene_{scene_id}.jpg"
            if download_image(image_url, file_path):
                success_count += 1

            # Rate limiting delay
            time.sleep(delay_seconds)

        except Exception as e:
            print(f"Error processing scene {idx}: {e}")
            continue

    print(f"Image generation completed. {success_count}/{len(data['visual_script'])} images generated.")
    return success_count > 0


# Backward compatibility wrapper
def main_generate_images_legacy(script_path: str, images_output_path: str):
    """
    Legacy function signature for backward compatibility.
    Loads API key from environment.
    """
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("openai_api_key")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return main_generate_images(
        Path(script_path),
        Path(images_output_path),
        api_key
    )
