def compare_campaign_list_equality(obtained, expected, offset: int = 0, client_id: int | None = None):
    for index in range(len(obtained)):
        item = obtained[index]
        name = item["name"] if isinstance(item, dict) else item.name
        item_client_id = item["client_id"] if isinstance(item, dict) else item.client_id
        assert name == expected[index + offset].name
        assert item_client_id is not None
        if client_id is not None:
            assert item_client_id == client_id