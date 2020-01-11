import DiscordNotifier as target


def dicts_are_equal(d1: dict, d2: dict):
    assert len(d1) == len(d2)
    for k, v in d1.items():
        assert k in d2
        assert d2[k] == v
    return


class TestStringToDict:

    def test_simple(self):
        # setup
        d = {"User123Xx": 0, "User_007": -19, "88User___": 7}
        s = "User123Xx:0,User_007:-19,88User___:7"
        d2 = target.string_to_dict(s)

        # testing
        dicts_are_equal(d, d2)
        return

    def test_special_chars(self):
        # setup
        d = {"User123Xx": 0, "User_007": -19, "88User___": 7}
        s = "\n User123Xx : 0,  User_007 \r\n: -19, 88 User___ : 7 \r\n"
        d2 = target.string_to_dict(s)

        # testing
        dicts_are_equal(d, d2)
        return


def test_dict_to_string():
    # setup
    d = {"User123Xx": 0, "User_007": -19, "88User___": 7}
    s = "88User___: +7,  User123Xx: 0,  User_007: -19"
    s2 = target.dict_to_string(d)

    # testing
    assert s == s2
    return


def test_dict_to_string_to_dict():
    # setup
    d = {"User123Xx": 0, "User_007": -19, "88User___": 7}
    s = "88User___: +7,  User123Xx: 0,  User_007: -19"
    s2 = target.dict_to_string(d)
    d2 = target.string_to_dict(s2)

    # testing
    dicts_are_equal(d, d2)
    return


def test_string_to_dict_to_string():
    # setup
    d = {"User123Xx": 0, "User_007": -19, "88User___": 7}
    s = "88User___: +7,  User123Xx: 0,  User_007: -19"
    d2 = target.string_to_dict(s)
    s2 = target.dict_to_string(d2)

    # testing
    assert s == s2
    return


def test_update_score():
    # setup
    score = {"User123Xx": 0, "User_007": -19, "88User___": 7, "BunnyXY": -3}
    update = {"User123Xx": -4, "User_007": +9, "88User___": -7, "MrBsg66": 6, "BunnyXY": 4}
    expected = {"User123Xx": -4, "User_007": -10, "MrBsg66": 6, "BunnyXY": 1}
    target.update_score(score, update)

    # testing
    dicts_are_equal(score, expected)
    return

