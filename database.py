import os
import motor.motor_asyncio

class Database:
    def __init__(self):
        mongo_url = os.environ.get("MONGO_URL")
        if not mongo_url:
            print("WARNING: MONGO_URL not found! Database will not work.")
            self.db = None
            return
            
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.db = self.client["TelegramBotDB"]
        self.warnings = self.db["warnings"]
        self.warnings = self.db["warnings"]
        self.whitelist = self.db["whitelist"]
        self.blacklist = self.db["blacklist"]

    # --- Warnings ---
    async def get_warnings(self, user_id):
        if self.db is None: return 0
        user = await self.warnings.find_one({"user_id": user_id})
        return user["count"] if user else 0

    async def add_warning(self, user_id):
        if self.db is None: return 0
        user = await self.warnings.find_one({"user_id": user_id})
        if user:
            new_count = user["count"] + 1
            await self.warnings.update_one({"user_id": user_id}, {"$set": {"count": new_count}})
            return new_count
        else:
            await self.warnings.insert_one({"user_id": user_id, "count": 1})
            return 1

    async def reset_warnings(self, user_id):
        if self.db is None: return
        await self.warnings.delete_one({"user_id": user_id})

    # --- Whitelist ---
    async def add_whitelist_domain(self, domain):
        if self.db is None: return
        await self.whitelist.update_one(
            {"type": "domain"}, 
            {"$addToSet": {"list": domain}}, 
            upsert=True
        )

    async def remove_whitelist_domain(self, domain):
        if self.db is None: return
        await self.whitelist.update_one(
            {"type": "domain"}, 
            {"$pull": {"list": domain}}
        )

    async def is_domain_whitelisted(self, text):
        if self.db is None: return False
        doc = await self.whitelist.find_one({"type": "domain"})
        if not doc or "list" not in doc:
            return False
        
        for domain in doc["list"]:
            if domain in text:
                return True
        return False

    async def add_whitelist_user(self, user_id):
        if self.db is None: return
        await self.whitelist.update_one(
            {"type": "user"}, 
            {"$addToSet": {"list": user_id}}, 
            upsert=True
        )

    async def remove_whitelist_user(self, user_id):
        if self.db is None: return
        await self.whitelist.update_one(
            {"type": "user"}, 
            {"$pull": {"list": user_id}}
        )

    async def is_user_whitelisted(self, user_id):
        if self.db is None: return False
        doc = await self.whitelist.find_one({"type": "user"})
        if not doc or "list" not in doc:
            return False
        return user_id in doc["list"]

    async def get_whitelist_domains(self):
        if self.db is None: return []
        doc = await self.whitelist.find_one({"type": "domain"})
        return doc["list"] if doc and "list" in doc else []

    async def get_whitelist_users(self):
        if self.db is None: return []
        doc = await self.whitelist.find_one({"type": "user"})
        return doc["list"] if doc and "list" in doc else []

    # --- Blacklist ---
    async def add_blacklist_word(self, word):
        if self.db is None: return
        await self.blacklist.update_one(
            {"type": "word"}, 
            {"$addToSet": {"list": word.lower()}}, 
            upsert=True
        )

    async def remove_blacklist_word(self, word):
        if self.db is None: return
        await self.blacklist.update_one(
            {"type": "word"}, 
            {"$pull": {"list": word.lower()}}
        )

    async def get_blacklist(self):
        if self.db is None: return []
        doc = await self.blacklist.find_one({"type": "word"})
        return doc["list"] if doc and "list" in doc else []
