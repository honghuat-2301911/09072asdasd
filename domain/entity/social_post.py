from dataclasses import dataclass, field
from typing import List


@dataclass
class Comment:

    id: int
    post_id: int
    user: str
    content: str
    profile_picture: str = ""

    # Getters
    def get_id(self):
        return self.id

    def get_post_id(self):
        return self.post_id

    def get_user(self):
        return self.user

    def get_content(self):
        return self.content

    def get_profile_picture(self):
        return self.profile_picture

    # Setters
    def set_id(self, id):
        self.id = id

    def set_post_id(self, post_id):
        self.post_id = post_id

    def set_user(self, user):
        self.user = user

    def set_content(self, content):
        self.content = content

    def set_profile_picture(self, profile_picture):
        self.profile_picture = profile_picture


@dataclass
class Post:

    id: int
    user: str
    content: str
    image_url: str
    likes: int
    comments: List[Comment] = field(default_factory=list)
    like_user_ids: str = ""

    # Getters
    def get_id(self):
        return self.id

    def get_user(self):
        return self.user

    def get_content(self):
        return self.content

    def get_image_url(self):
        return self.image_url

    def get_likes(self):
        return self.likes

    def get_comments(self):
        return self.comments

    def get_like_user_ids(self):
        return self.like_user_ids

    # Setters
    def set_id(self, id):
        self.id = id

    def set_user(self, user):
        self.user = user

    def set_content(self, content):
        self.content = content

    def set_image_url(self, image_url):
        self.image_url = image_url

    def set_likes(self, likes):
        self.likes = likes

    def set_comments(self, comments):
        self.comments = comments

    def set_like_user_ids(self, like_user_ids):
        self.like_user_ids = like_user_ids
