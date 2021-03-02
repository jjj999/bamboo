import hug


@hug.get("/test", output_format=hug.output_format.text, parse_body=False)
def text():
    return "Hello, World!"
