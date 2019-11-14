# sremail

'SRE Mail' is a Python package designed to make sending email to SaaS in MIME 
format to the different clusters a lot easier.

## Basic usage

```python
from datetime import datetime

from sremail import message, smtp

msg = message.Message(to=["Sam Gibson <sgibson@glasswallsolutions.com>", "a@b.com"],
                      from_addresses=["another@email.com"],
                      date=datetime.now(),
                      another_header="test")
             .attach("attachment.pdf")

smtp.send(msg, "smtp.some_server.com:25")
```

## Gotchas
- You can't add the `X-FileTrust-Tenant` header to a `Message` with a kwarg, as there's no way to format it in a general way due to the capitalised 'T' in 'Trust'. To get around this you have to add the header manually:
    ```python
    msg = message.Message(to=["Sam Gibson <sgibson@glasswallsolutions.com>", "a@b.com"],
                      from_addresses=["another@email.com"],
                      date=datetime.now())
    msg.headers["X-FileTrust-Tenant"] = "<guid>"
    ```

## Development

### Prerequisites
- Python 3.7
- Pipenv

### Quick start
1. Clone this repo.
2. Run `pipenv sync`.
3. You're good to go. You can run commands using the package inside a
   `pipenv shell`, and modify the code with your IDE.