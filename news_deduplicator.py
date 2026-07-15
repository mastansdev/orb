import hashlib
import re

class NewsDeduplicator:
    """
    Determines whether incoming news has already been processed
    using normalized textual features.
    """

    def _normalize_text(self, text: str) -> str:
        # Lowercase, strip whitespace, and remove all non-alphanumeric characters
        text = text.lower().strip()
        return re.sub(r'[^a-z0-9\s]', '', text)

    def build_hash(self, news) -> str:
        # Focus heavily on the content rather than the metadata
        normalized_headline = self._normalize_text(news.headline)
        
        # Combine core features for the unique signature
        features = f"{normalized_headline}|{news.source.value.lower()}"
        
        return hashlib.sha256(features.encode('utf-8')).hexdigest()

    def is_duplicate(self, news, known_hashes) -> bool:
        """
        Checks if the incoming news item's hash exists in the collection 
        of already processed hashes.
        """
        news_hash = self.build_hash(news)
        return news_hash in known_hashes