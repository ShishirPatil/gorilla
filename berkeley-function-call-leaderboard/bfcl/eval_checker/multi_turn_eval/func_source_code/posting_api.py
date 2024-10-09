from typing import Dict, List, Optional, Union


class TwitterAPI:
    def __init__(self):
        self.username: str = "john"
        self.password: str = "john1234"
        self.authenticated: bool = False
        self.tweets: Dict[int, Dict[str, Union[int, str, List[str]]]] = {}
        self.comments: Dict[int, List[Dict[str, str]]] = {}
        self.retweets: Dict[str, List[int]] = {}
        self.following_list: List[str] = ["alice", "bob"]
        self.tweet_counter: int = 1

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the TwitterAPI instance.
        Args:
            scenario (dict): A dictionary containing Twitter data.
        """
        self.username = scenario.get("username", "john")
        self.password = scenario.get("password", "john1234")
        self.authenticated = scenario.get("authenticated", False)
        self.tweets = scenario.get("tweets", {})
        self.comments = scenario.get("comments", {})
        self.retweets = scenario.get("retweets", {})
        self.following_list = scenario.get("following_list", ["alice", "bob"])
        self.tweet_counter = scenario.get("tweet_counter", 1)

    def authenticate_twitter(self, username: str, password: str) -> Dict[str, bool]:
        """
        Authenticate a user with username and password. Always authenticate the user first.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.
        Returns:
            authentication_status (bool): True if authenticated, False otherwise.
        """
        if username == self.username and password == self.password:
            self.authenticated = True
            return {"authentication_status": True}
        return {"authentication_status": False}

    def post_tweet(
        self, content: str, tags: List[str] = [], mentions: List[str] = []
    ) -> Dict[str, Union[int, str, List[str]]]:
        """
        Post a tweet for the authenticated user.

        Args:
            content (str): Content of the tweet.
            tags (List[str]): List of tags for the tweet. Tag name should start with #.
            mentions (List[str]): List of users mentioned in the tweet. Mention name should start with @.
        Returns:
            id (int): ID of the posted tweet.
            username (str): Username of the poster.
            content (str): Content of the tweet.
            tags (List[str]): List of tags associated with the tweet.
            mentions (List[str]): List of users mentioned in the tweet.
        """
        if not self.authenticated:
            raise ValueError("User not authenticated. Please authenticate before posting.")

        tweet = {
            "id": self.tweet_counter,
            "username": self.username,
            "content": content,
            "tags": tags,
            "mentions": mentions,
        }
        self.tweets[self.tweet_counter] = tweet
        self.tweet_counter += 1
        return tweet

    def retweet(self, tweet_id: int) -> Dict[str, str]:
        """
        Retweet a tweet for the authenticated user.

        Args:
            tweet_id (int): ID of the tweet to retweet.
        Returns:
            retweet_status (str): Status of the retweet action.
        """
        if not self.authenticated:
            raise ValueError(
                "User not authenticated. Please authenticate before retweeting."
            )

        if tweet_id not in self.tweets:
            return {"error": f"Tweet with ID {tweet_id} not found."}

        if self.username not in self.retweets:
            self.retweets[self.username] = []

        if tweet_id in self.retweets[self.username]:
            return {"retweet_status": "Already retweeted"}

        self.retweets[self.username].append(tweet_id)
        return {"retweet_status": "Successfully retweeted"}

    def comment(self, tweet_id: int, comment_content: str) -> Dict[str, str]:
        """
        Comment on a tweet for the authenticated user.

        Args:
            tweet_id (int): ID of the tweet to comment on.
            comment_content (str): Content of the comment.
        Returns:
            comment_status (str): Status of the comment action.
        """
        if not self.authenticated:
            raise ValueError(
                "User not authenticated. Please authenticate before commenting."
            )

        if tweet_id not in self.tweets:
            return {"error": f"Tweet with ID {tweet_id} not found."}

        if tweet_id not in self.comments:
            self.comments[tweet_id] = []

        self.comments[tweet_id].append(
            {"username": self.username, "content": comment_content}
        )
        return {"comment_status": "Comment added successfully"}

    def mention(self, tweet_id: int, mentioned_usernames: List[str]) -> Dict[str, str]:
        """
        Mention specified users in a tweet.

        Args:
            tweet_id (int): ID of the tweet where users are mentioned.
            mentioned_usernames (List[str]): List of usernames to be mentioned.
        Returns:
            mention_status (str): Status of the mention action.
        """
        if tweet_id not in self.tweets:
            return {"error": f"Tweet with ID {tweet_id} not found."}

        tweet = self.tweets[tweet_id]
        tweet["mentions"].extend(mentioned_usernames)

        return {"mention_status": "Users mentioned successfully"}

    def follow_user(self, username_to_follow: str) -> Dict[str, bool]:
        """
        Follow a user for the authenticated user.

        Args:
            username_to_follow (str): Username of the user to follow.
        Returns:
            follow_status (bool): True if followed, False if already following.
        """
        if not self.authenticated:
            raise ValueError(
                "User not authenticated. Please authenticate before following."
            )

        if username_to_follow in self.following_list:
            return {"follow_status": False}
        self.following_list.append(username_to_follow)
        return {"follow_status": True}

    def list_all_following(self) -> List[str]:
        """
        List all users that the authenticated user is following.

        Args:
            None
        Returns:
            following_list (List[str]): List of all users that the authenticated user is following.
        """
        if not self.authenticated:
            raise ValueError(
                "User not authenticated. Please authenticate before listing following."
            )
        return self.following_list

    def unfollow_user(self, username_to_unfollow: str) -> Dict[str, bool]:
        """
        Unfollow a user for the authenticated user.

        Args:
            username_to_unfollow (str): Username of the user to unfollow.
        Returns:
            unfollow_status (bool): True if unfollowed, False if not following.
        """
        if not self.authenticated:
            raise ValueError(
                "User not authenticated. Please authenticate before unfollowing."
            )

        if username_to_unfollow not in self.following_list:
            return {"unfollow_status": False}
        self.following_list.remove(username_to_unfollow)
        return {"unfollow_status": True}

    def get_tweet(self, tweet_id: int) -> Optional[Dict[str, Union[int, str, List[str]]]]:
        """
        Retrieve a specific tweet.

        Args:
            tweet_id (int): ID of the tweet to retrieve.
        Returns:
            id (int): ID of the retrieved tweet.
            username (str): Username of the tweet's author.
            content (str): Content of the tweet.
            tags (List[str]): List of tags associated with the tweet.
            mentions (List[str]): List of users mentioned in the tweet.
        """
        if tweet_id not in self.tweets:
            return {"error": f"Tweet with ID {tweet_id} not found."}
        return self.tweets[tweet_id]

    def get_user_tweets(self, username: str) -> List[Dict[str, Union[int, str, List[str]]]]:
        """
        Retrieve all tweets from a specific user.

        Args:
            username (str): Username of the user whose tweets to retrieve.
        Returns:
            user_tweets (List[Dict]): List of dictionaries, each containing tweet information.
        """
        return [tweet for tweet in self.tweets.values() if tweet["username"] == username]

    def search_tweets(self, keyword: str) -> List[Dict[str, Union[int, str, List[str]]]]:
        """
        Search for tweets containing a specific keyword.

        Args:
            keyword (str): Keyword to search for in tweets.
        Returns:
            matching_tweets (List[Dict]): List of dictionaries, each containing tweet information.
        """
        return [
            tweet
            for tweet in self.tweets.values()
            if keyword.lower() in tweet["content"].lower()
            or keyword.lower() in [tag.lower() for tag in tweet["tags"]]
        ]

    def get_tweet_comments(self, tweet_id: int) -> List[Dict[str, str]]:
        """
        Retrieve all comments for a specific tweet.

        Args:
            tweet_id (int): ID of the tweet to retrieve comments for.
        Returns:
            comments (List[Dict]): List of dictionaries, each containing comment information.
        """
        if tweet_id not in self.tweets:
            return {"error": f"Tweet with ID {tweet_id} not found."}
        return self.comments.get(tweet_id, [])

    def get_user_stats(self, username: str) -> Dict[str, int]:
        """
        Get statistics for a specific user.

        Args:
            username (str): Username of the user to get statistics for.
        Returns:
            tweet_count (int): Number of tweets posted by the user.
            following_count (int): Number of users the specified user is following.
            retweet_count (int): Number of retweets made by the user.
        """
        tweet_count = len(
            [tweet for tweet in self.tweets.values() if tweet["username"] == username]
        )
        following_count = len(self.following_list) if username == self.username else 0
        retweet_count = len(self.retweets.get(username, []))

        return {
            "tweet_count": tweet_count,
            "following_count": following_count,
            "retweet_count": retweet_count,
        }
