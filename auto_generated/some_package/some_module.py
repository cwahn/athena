from src.entoli.base.io import get_str
from src.entoli.base.io import put_strln



greet = (
    put_strln('What is your name?')
    .then(get_str)
    .and_then(lambda name: put_strln(f'Hello, {name}!'))
)