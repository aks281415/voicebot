import asyncio

# Typing animation effect
async def async_type_response(placeholder, response, delay=0.05):
    displayed = ""
    for char in response:
        displayed += char
        placeholder.markdown(displayed)
        await asyncio.sleep(delay)