# Recommendation System

Recommended to be used with PyCharm IDE.

Run below in the terminal to install the requirements and start the service:

```bash
# Install the requirements:
pip install -r requirements.txt
pip installl uvicorn

# Start the service:
uvicorn app:app --reload
```

Now you can load http://localhost:8000/docs in your browser ... but there won't be much to see until you've inserted
some data.

You can test with,

    existing_profile = "6444081c6114678ff14f7c97"

    new_profile = "6444081c6114610ff14f7c97"


rename 

    db = client.agriculture_test