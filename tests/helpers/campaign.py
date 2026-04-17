def compare_campaign_list_equality(obtained, expected, offset:int = 0):
    for index in range(len(obtained)):
        item = obtained[index]
        name = item["name"] if isinstance(item, dict) else item.name
        client = item["client"] if isinstance(item, dict) else item.client
        assert name == expected[index + offset].name
        assert client == expected[index + offset].client