"""
Publishing Agent
Handles automatic posting to social media platforms
"""
import json
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path
import openai
from .base_agent import BaseAgent


class PublishingAgent(BaseAgent):
    """Agent responsible for publishing videos to social media platforms"""
    
    def __init__(
        self,
        openai_api_key: str,
        youtube_credentials: Optional[Dict] = None,
        instagram_credentials: Optional[Dict] = None,
        tiktok_credentials: Optional[Dict] = None,
        linkedin_credentials: Optional[Dict] = None
    ):
        super().__init__("PublishingAgent")
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.youtube_creds = youtube_credentials or {}
        self.instagram_creds = instagram_credentials or {}
        self.tiktok_creds = tiktok_credentials or {}
        self.linkedin_creds = linkedin_credentials or {}
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish video to specified platforms
        
        Expected context:
            - video_path: Path to video file
            - title: Video title
            - summary: Video summary
            - topics: List of topics/tags
            - platforms: List of platforms to publish to
        
        Returns:
            - published: Dict of platform -> publish result
        """
        self.log_start("Publishing video to social media platforms")
        
        try:
            video_path = Path(context['video_path'])
            title = context.get('title', 'Untitled Video')
            summary = context.get('summary', '')
            topics = context.get('topics', [])
            platforms = context.get('platforms', [])
            
            # Use pre-generated metadata if available, otherwise generate
            pregenerated = context.get('pregenerated_metadata')
            if pregenerated and isinstance(pregenerated, dict) and 'youtube' in pregenerated:
                self.log_progress("Using pre-generated metadata")
                metadata = pregenerated
            else:
                self.log_progress("Generating platform-specific metadata")
                metadata = await self._generate_metadata(title, summary, topics)
            
            results = {}
            
            # Publish to each platform
            for platform in platforms:
                self.log_progress(f"Publishing to {platform}")
                
                if platform.lower() == 'youtube':
                    result = await self._publish_youtube(video_path, metadata)
                elif platform.lower() == 'instagram':
                    result = await self._publish_instagram(video_path, metadata)
                elif platform.lower() == 'tiktok':
                    result = await self._publish_tiktok(video_path, metadata)
                elif platform.lower() == 'linkedin':
                    result = await self._publish_linkedin(video_path, metadata)
                else:
                    result = {'success': False, 'error': f'Unknown platform: {platform}'}
                
                results[platform] = result
            
            self.log_complete(f"Published to {len(results)} platforms")
            
            return {'published': results, 'metadata': metadata}
            
        except Exception as e:
            self.log_error(f"Publishing failed: {str(e)}")
            raise

    
    async def _generate_metadata(
        self,
        title: str,
        summary: str,
        topics: List[str]
    ) -> Dict[str, Any]:
        """Generate platform-specific metadata using GPT-4"""
        
        prompt = f"""Generate social media metadata for this video:

Title: {title}
Summary: {summary}
Topics: {', '.join(topics)}

Generate:
1. YouTube Shorts title (max 100 chars)
2. YouTube description (engaging, with call-to-action)
3. Instagram caption (engaging, with emojis)
4. TikTok caption (trendy, with hashtags)
5. LinkedIn post text (professional tone)
6. Hashtags for each platform (relevant and trending)

Output as JSON."""
        
        system_prompt = """You are a social media expert. Generate platform-specific content. Output JSON:
{
  "youtube": {
    "title": "Engaging title",
    "description": "Description with CTA",
    "tags": ["tag1", "tag2", "tag3"]
  },
  "instagram": {
    "caption": "Caption with emojis",
    "hashtags": ["#hashtag1", "#hashtag2"]
  },
  "tiktok": {
    "caption": "Trendy caption",
    "hashtags": ["#hashtag1", "#hashtag2"]
  },
  "linkedin": {
    "text": "Professional post",
    "hashtags": ["#hashtag1", "#hashtag2"]
  }
}"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        metadata_text = response.choices[0].message.content
        
        # Extract JSON
        try:
            metadata = json.loads(metadata_text)
        except:
            import re
            json_match = re.search(r'```json\n(.*?)\n```', metadata_text, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group(1))
            else:
                # Fallback metadata
                metadata = self._create_fallback_metadata(title, topics)
        
        return metadata
    
    def _create_fallback_metadata(self, title: str, topics: List[str]) -> Dict[str, Any]:
        """Create fallback metadata if AI generation fails"""
        hashtags = [f"#{topic.replace(' ', '')}" for topic in topics[:5]]
        
        return {
            "youtube": {
                "title": title[:100],
                "description": f"{title}\n\nWatch more content like this!",
                "tags": topics[:10]
            },
            "instagram": {
                "caption": f"{title} 🎥✨",
                "hashtags": hashtags
            },
            "tiktok": {
                "caption": f"{title} #fyp",
                "hashtags": hashtags + ["#fyp", "#viral"]
            },
            "linkedin": {
                "text": f"{title}\n\nThoughts on this topic?",
                "hashtags": hashtags
            }
        }

    
    async def _publish_youtube(
        self,
        video_path: Path,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish to YouTube Shorts using YouTube Data API v3"""
        
        if not self.youtube_creds.get('api_key') and not self.youtube_creds.get('access_token'):
            self.log_progress("YouTube credentials not configured, skipping")
            return {'success': False, 'error': 'No YouTube credentials'}
        
        try:
            youtube_meta = metadata.get('youtube', {})
            access_token = self.youtube_creds.get('access_token', '')
            
            title = youtube_meta.get('title', 'Untitled')[:100]
            description = youtube_meta.get('description', '')
            tags = youtube_meta.get('tags', [])
            
            # Step 1: Initiate resumable upload
            init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
            
            video_metadata = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "25"  # News & Politics
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                    "madeForKids": False
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(video_path.stat().st_size)
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get resumable upload URI
                init_response = await client.post(
                    init_url,
                    json=video_metadata,
                    headers=headers
                )
                
                if init_response.status_code not in (200, 201):
                    error_detail = init_response.text
                    self.log_error(f"YouTube init failed: {init_response.status_code} - {error_detail}")
                    return {'success': False, 'error': f"Init failed: {init_response.status_code} - {error_detail}"}
                
                upload_uri = init_response.headers.get('Location')
                if not upload_uri:
                    return {'success': False, 'error': 'No upload URI returned'}
                
                self.log_progress(f"Got upload URI, uploading video ({video_path.stat().st_size // 1024 // 1024}MB)...")
            
            # Step 2: Upload video file (separate client for large file)
            async with httpx.AsyncClient(timeout=600.0) as client:
                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()
                
                upload_response = await client.put(
                    upload_uri,
                    content=video_data,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(video_data))
                    }
                )
                
                if upload_response.status_code in (200, 201):
                    result = upload_response.json()
                    video_id = result.get('id')
                    self.log_progress(f"YouTube upload successful: {video_id}")
                    return {
                        'success': True,
                        'video_id': video_id,
                        'url': f"https://youtube.com/shorts/{video_id}"
                    }
                else:
                    error_detail = upload_response.text
                    self.log_error(f"YouTube upload failed: {upload_response.status_code} - {error_detail}")
                    return {
                        'success': False,
                        'error': f"Upload failed: {upload_response.status_code} - {error_detail}"
                    }
        
        except Exception as e:
            self.log_error(f"YouTube upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _publish_instagram(
        self,
        video_path: Path,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish to Instagram Reels using Instagram Graph API"""
        
        if not self.instagram_creds.get('access_token'):
            self.log_progress("Instagram credentials not configured, skipping")
            return {'success': False, 'error': 'No Instagram credentials'}
        
        try:
            instagram_meta = metadata.get('instagram', {})
            caption = instagram_meta.get('caption', '')
            hashtags = ' '.join(instagram_meta.get('hashtags', []))
            full_caption = f"{caption}\n\n{hashtags}"
            
            # Instagram Graph API endpoint
            ig_user_id = self.instagram_creds.get('user_id')
            access_token = self.instagram_creds.get('access_token')
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Create media container
                create_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
                
                # Upload video to a publicly accessible URL first (required by Instagram)
                # Note: You'll need to implement video hosting or use a service
                video_url = await self._upload_to_hosting(video_path)
                
                create_params = {
                    'video_url': video_url,
                    'caption': full_caption,
                    'media_type': 'REELS',
                    'access_token': access_token
                }
                
                create_response = await client.post(create_url, params=create_params)
                
                if create_response.status_code == 200:
                    container_id = create_response.json().get('id')
                    
                    # Step 2: Publish the media
                    publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
                    publish_params = {
                        'creation_id': container_id,
                        'access_token': access_token
                    }
                    
                    publish_response = await client.post(publish_url, params=publish_params)
                    
                    if publish_response.status_code == 200:
                        media_id = publish_response.json().get('id')
                        self.log_progress(f"Instagram upload successful: {media_id}")
                        return {
                            'success': True,
                            'media_id': media_id
                        }
                
                return {
                    'success': False,
                    'error': 'Upload failed'
                }
        
        except Exception as e:
            self.log_error(f"Instagram upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _publish_tiktok(
        self,
        video_path: Path,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish to TikTok using TikTok API"""
        
        if not self.tiktok_creds.get('access_token'):
            self.log_progress("TikTok credentials not configured, skipping")
            return {'success': False, 'error': 'No TikTok credentials'}
        
        try:
            tiktok_meta = metadata.get('tiktok', {})
            caption = tiktok_meta.get('caption', '')
            
            # TikTok Content Posting API
            # Note: Requires TikTok for Developers approval
            upload_url = "https://open-api.tiktok.com/share/video/upload/"
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(video_path, 'rb') as video_file:
                    files = {'video': video_file}
                    data = {
                        'description': caption,
                        'privacy_level': 'PUBLIC_TO_EVERYONE'
                    }
                    headers = {
                        'Authorization': f"Bearer {self.tiktok_creds['access_token']}"
                    }
                    
                    response = await client.post(
                        upload_url,
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_progress("TikTok upload successful")
                        return {
                            'success': True,
                            'share_id': result.get('share_id')
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Upload failed: {response.status_code}"
                        }
        
        except Exception as e:
            self.log_error(f"TikTok upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _publish_linkedin(
        self,
        video_path: Path,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish to LinkedIn using LinkedIn API"""
        
        if not self.linkedin_creds.get('access_token'):
            self.log_progress("LinkedIn credentials not configured, skipping")
            return {'success': False, 'error': 'No LinkedIn credentials'}
        
        try:
            linkedin_meta = metadata.get('linkedin', {})
            text = linkedin_meta.get('text', '')
            hashtags = ' '.join(linkedin_meta.get('hashtags', []))
            full_text = f"{text}\n\n{hashtags}"
            
            # LinkedIn API endpoint
            person_urn = self.linkedin_creds.get('person_urn')
            access_token = self.linkedin_creds.get('access_token')
            
            # LinkedIn video upload is a multi-step process
            # 1. Register upload
            # 2. Upload video
            # 3. Create post
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Register upload
                register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
                register_data = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                        "owner": person_urn,
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }]
                    }
                }
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                register_response = await client.post(
                    register_url,
                    json=register_data,
                    headers=headers
                )
                
                if register_response.status_code == 200:
                    upload_info = register_response.json()
                    asset_urn = upload_info['value']['asset']
                    upload_url = upload_info['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                    
                    # Step 2: Upload video
                    with open(video_path, 'rb') as video_file:
                        upload_response = await client.put(
                            upload_url,
                            content=video_file.read(),
                            headers={'Authorization': f'Bearer {access_token}'}
                        )
                    
                    if upload_response.status_code == 201:
                        # Step 3: Create post
                        post_url = "https://api.linkedin.com/v2/ugcPosts"
                        post_data = {
                            "author": person_urn,
                            "lifecycleState": "PUBLISHED",
                            "specificContent": {
                                "com.linkedin.ugc.ShareContent": {
                                    "shareCommentary": {
                                        "text": full_text
                                    },
                                    "shareMediaCategory": "VIDEO",
                                    "media": [{
                                        "status": "READY",
                                        "media": asset_urn
                                    }]
                                }
                            },
                            "visibility": {
                                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                            }
                        }
                        
                        post_response = await client.post(
                            post_url,
                            json=post_data,
                            headers=headers
                        )
                        
                        if post_response.status_code == 201:
                            post_id = post_response.json().get('id')
                            self.log_progress(f"LinkedIn upload successful: {post_id}")
                            return {
                                'success': True,
                                'post_id': post_id
                            }
                
                return {
                    'success': False,
                    'error': 'Upload failed'
                }
        
        except Exception as e:
            self.log_error(f"LinkedIn upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_to_hosting(self, video_path: Path) -> str:
        """
        Upload video to a hosting service and return public URL
        This is required for Instagram API
        You can use AWS S3, Cloudinary, or similar service
        """
        # TODO: Implement actual video hosting
        # For now, return a placeholder
        self.log_progress("Video hosting not implemented, using placeholder URL")
        return f"https://example.com/videos/{video_path.name}"
