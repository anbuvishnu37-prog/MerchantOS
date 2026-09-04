from app.ai_agent import ask_merchantos_ai


def test_ai_agent_places_order():

    question = """
    I want to buy 1 Wireless Mouse.
    Please place the order for me.
    """

    response = ask_merchantos_ai(question)

    assert response is not None
    assert "Order placed successfully" in response
    assert "Wireless Mouse" in response
    assert "799" in response
    assert "PENDING" in response