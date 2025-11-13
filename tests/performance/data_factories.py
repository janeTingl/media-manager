"""Synthetic data factories for performance testing."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from sqlmodel import Session

from src.media_manager.persistence.models import (
    Artwork,
    Collection,
    Credit,
    Favorite,
    Library,
    MediaFile,
    MediaItem,
    Person,
    Tag,
    MediaItemTag,
    MediaItemCollection,
)


class SyntheticDataFactory:
    """Factory for generating synthetic test data."""
    
    def __init__(self, session: Session):
        self.session = session
        self._persons_cache: List[Person] = []
        self._tags_cache: List[Tag] = []
        self._collections_cache: List[Collection] = []
        
    def create_library(self, name: str = "Test Library", **kwargs) -> Library:
        """Create a synthetic library."""
        library = Library(
            name=name,
            path=kwargs.get("path", f"/libraries/{name.lower().replace(' ', '_')}"),
            media_type=kwargs.get("media_type", "mixed"),
        )
        self.session.add(library)
        self.session.flush()
        return library
    
    def create_persons(self, count: int = 100) -> List[Person]:
        """Create synthetic persons."""
        if self._persons_cache:
            return self._persons_cache[:count]
            
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Chris", "Lisa", "Robert", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        for i in range(count):
            # Ensure unique names
            first_name = first_names[i % len(first_names)]
            last_name = last_names[(i // len(first_names)) % len(last_names)]
            unique_suffix = i // (len(first_names) * len(last_names))
            
            name = f"{first_name} {last_name}"
            if unique_suffix > 0:
                name += f" {unique_suffix}"
            
            person = Person(
                name=name,
                external_id=f"person_{i}",
                biography=f"Biography for person {i}. " * 5,
            )
            self.session.add(person)
            self._persons_cache.append(person)
        
        self.session.flush()
        return self._persons_cache
    
    def create_tags(self, count: int = 50) -> List[Tag]:
        """Create synthetic tags."""
        if self._tags_cache:
            return self._tags_cache[:count]
            
        tag_names = [
            "Action", "Adventure", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller",
            "Romance", "Mystery", "Fantasy", "Animation", "Documentary", "Biography",
            "Crime", "Family", "History", "Music", "War", "Western", "Musical",
            "Short", "Sport", "Talk-Show", "News", "Reality-TV", "Game-Show",
            "Adult", "Film-Noir", "Classic", "Modern", "Indie", "Blockbuster",
        ]
        
        for i in range(min(count, len(tag_names))):
            tag = Tag(
                name=tag_names[i],
                description=f"Description for {tag_names[i]} tag",
                color=f"#{random.randint(0, 0xFFFFFF):06x}",
            )
            self.session.add(tag)
            self._tags_cache.append(tag)
        
        # Create additional unique tags if needed
        for i in range(len(tag_names), count):
            tag = Tag(
                name=f"Tag {i}",
                description=f"Description for tag {i}",
                color=f"#{random.randint(0, 0xFFFFFF):06x}",
            )
            self.session.add(tag)
            self._tags_cache.append(tag)
        
        self.session.flush()
        return self._tags_cache
    
    def create_collections(self, count: int = 20) -> List[Collection]:
        """Create synthetic collections."""
        if self._collections_cache:
            return self._collections_cache[:count]
            
        collection_names = [
            "Marvel Cinematic Universe", "Star Wars Saga", "Harry Potter Series",
            "James Bond Collection", "Fast & Furious", "The Lord of the Rings",
            "Mission Impossible", "X-Men Series", "DC Extended Universe",
            "Pixar Animation Studios", "Disney Classics", "Studio Ghibli",
            "Christopher Nolan Films", "Quentin Tarantino Films",
            "Marvel Netflix Series", "Star Trek Collection", "Batman Series",
            "Spider-Man Films", "Superhero Collection", "Award Winners",
        ]
        
        for i in range(min(count, len(collection_names))):
            collection = Collection(
                name=collection_names[i],
                description=f"Description for {collection_names[i]} collection",
                sort_order=i,
            )
            self.session.add(collection)
            self._collections_cache.append(collection)
        
        # Create additional unique collections if needed
        for i in range(len(collection_names), count):
            collection = Collection(
                name=f"Collection {i}",
                description=f"Description for collection {i}",
                sort_order=i,
            )
            self.session.add(collection)
            self._collections_cache.append(collection)
        
        self.session.flush()
        return self._collections_cache
    
    def create_media_item(
        self, 
        library_id: int, 
        item_index: int = 0,
        media_type: str = None,
        **kwargs
    ) -> MediaItem:
        """Create a synthetic media item."""
        if media_type is None:
            media_type = random.choice(["movie", "tv", "tv"])
        
        # Generate title
        titles = [
            "The Adventure", "Mystery of", "Journey to", "Secret of", "Legend of",
            "Return of", "Battle for", "Quest for", "Curse of", "Treasure of",
        ]
        subtitles = [
            "the Lost City", "the Hidden Temple", "the Ancient artifact",
            "the Forgotten Realm", "the Unknown", "the Shadows", "the Light",
            "the Darkness", "the Final Chapter", "the Beginning",
        ]
        
        title = f"{random.choice(titles)} {random.choice(subtitles)} {item_index}"
        
        # Generate metadata
        year = kwargs.get("year", random.randint(1990, 2024))
        genres = json.dumps(random.sample([
            "Action", "Adventure", "Comedy", "Drama", "Horror", "Sci-Fi",
            "Thriller", "Romance", "Mystery", "Fantasy", "Animation",
        ], k=random.randint(1, 3)))
        
        media_item = MediaItem(
            library_id=library_id,
            title=title,
            media_type=media_type,
            year=year,
            description=f"Description for {title}. " * random.randint(3, 10),
            genres=genres,
            runtime=random.randint(80, 180) if media_type == "movie" else random.randint(20, 60),
            rating=round(random.uniform(5.0, 9.5), 1),
            season=None if media_type == "movie" else random.randint(1, 10),
            episode=None if media_type == "movie" else random.randint(1, 24),
            external_id=f"external_{item_index}",
            provider=random.choice(["tmdb", "tvdb"]),
        )
        
        self.session.add(media_item)
        self.session.flush()
        return media_item
    
    def create_media_file(self, media_item_id: int, **kwargs) -> MediaFile:
        """Create a synthetic media file."""
        media_file = MediaFile(
            media_item_id=media_item_id,
            path=kwargs.get("path", f"/media/item_{media_item_id}.mp4"),
            filename=kwargs.get("filename", f"item_{media_item_id}.mp4"),
            file_size=kwargs.get("file_size", random.randint(500_000_000, 3_000_000_000)),  # 500MB - 3GB
            duration=kwargs.get("duration", random.randint(1200, 7200)),  # 20-120 minutes
            container=kwargs.get("container", random.choice(["mp4", "mkv", "avi"])),
            video_codec=kwargs.get("video_codec", random.choice(["h264", "h265", "vp9"])),
            audio_codec=kwargs.get("audio_codec", random.choice(["aac", "ac3", "dts"])),
            resolution=kwargs.get("resolution", random.choice(["1920x1080", "3840x2160", "1280x720"])),
        )
        self.session.add(media_file)
        return media_file
    
    def create_artwork(self, media_item_id: int, artwork_type: str = "poster", **kwargs) -> Artwork:
        """Create synthetic artwork."""
        artwork = Artwork(
            media_item_id=media_item_id,
            artwork_type=artwork_type,
            url=kwargs.get("url", f"https://example.com/{artwork_type}/{media_item_id}.jpg"),
            size=kwargs.get("size", random.choice(["thumb", "original", "large"])),
            download_status=kwargs.get("download_status", "completed"),
        )
        self.session.add(artwork)
        return artwork
    
    def create_credit(
        self, 
        media_item_id: int, 
        person_id: int, 
        role: str = "actor",
        **kwargs
    ) -> Credit:
        """Create a synthetic credit."""
        character_name = None
        if role == "actor":
            character_name = f"Character {random.randint(1, 100)}"
        
        credit = Credit(
            media_item_id=media_item_id,
            person_id=person_id,
            role=role,
            character_name=character_name,
            order=kwargs.get("order", random.randint(1, 20)),
        )
        self.session.add(credit)
        return credit
    
    def create_favorite(self, media_item_id: int, user_id: str = "test_user") -> Favorite:
        """Create a synthetic favorite."""
        favorite = Favorite(
            media_item_id=media_item_id,
            user_id=user_id,
            added_at=datetime.utcnow(),
        )
        self.session.add(favorite)
        return favorite
    
    def create_media_item_tag(self, media_item_id: int, tag_id: int) -> MediaItemTag:
        """Create a media item tag relationship."""
        media_item_tag = MediaItemTag(
            media_item_id=media_item_id,
            tag_id=tag_id,
        )
        self.session.add(media_item_tag)
        return media_item_tag
    
    def create_media_item_collection(self, media_item_id: int, collection_id: int) -> MediaItemCollection:
        """Create a media item collection relationship."""
        media_item_collection = MediaItemCollection(
            media_item_id=media_item_id,
            collection_id=collection_id,
        )
        self.session.add(media_item_collection)
        return media_item_collection
    
    def create_synthetic_library(
        self, 
        item_count: int = 1000,
        library_name: str = "Synthetic Library",
        with_tags: bool = True,
        with_collections: bool = True,
        with_favorites: bool = True,
        with_credits: bool = True,
        batch_size: int = 100,
    ) -> Library:
        """Create a complete synthetic library with all related data."""
        print(f"Creating synthetic library with {item_count} items...")
        
        # Create library
        library = self.create_library(library_name)
        
        # Create supporting data
        if with_credits:
            persons = self.create_persons(min(100, item_count // 10))
        
        if with_tags:
            tags = self.create_tags(min(50, item_count // 20))
        
        if with_collections:
            collections = self.create_collections(min(20, item_count // 50))
        
        # Create media items in batches
        for batch_start in range(0, item_count, batch_size):
            batch_end = min(batch_start + batch_size, item_count)
            batch_items = []
            
            for i in range(batch_start, batch_end):
                # Create media item
                media_item = self.create_media_item(library.id, i)
                batch_items.append(media_item)
                
                # Create media file
                self.create_media_file(media_item.id)
                
                # Create artworks
                for artwork_type in ["poster", "fanart"]:
                    self.create_artwork(media_item.id, artwork_type)
                
                # Create credits
                if with_credits and persons:
                    for j in range(random.randint(3, 8)):
                        person = random.choice(persons)
                        role = random.choice(["actor"] * 5 + ["director", "writer", "producer"])
                        self.create_credit(media_item.id, person.id, role)
                
                # Add tags
                if with_tags and tags:
                    selected_tags = random.sample(tags, random.randint(1, min(5, len(tags))))
                    for tag in selected_tags:
                        self.create_media_item_tag(media_item.id, tag.id)
                
                # Add to collections
                if with_collections and collections:
                    selected_collections = random.sample(
                        collections, random.randint(0, min(3, len(collections)))
                    )
                    for collection in selected_collections:
                        self.create_media_item_collection(media_item.id, collection.id)
                
                # Mark as favorite
                if with_favorites and random.random() < 0.1:  # 10% favorites
                    self.create_favorite(media_item.id)
            
            # Commit batch
            self.session.commit()
            
            # Progress
            progress = batch_end
            percentage = (progress / item_count) * 100
            print(f"  Progress: {progress}/{item_count} ({percentage:.1f}%)")
        
        print(f"Created synthetic library with {item_count} items")
        return library