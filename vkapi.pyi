class VkAPI:
    """Враппер для VK_API"""
    # https://vk.com/dev/wall.get
    def wall_get(self, owner_id: int = None, domain: str = None, offset: int = None, count: int = None) -> dict: ...
