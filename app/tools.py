TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_projects",
            "description": "Fetch a list of my projects, including links, descriptions, and technologies used. Use this to provide information about the projects I've built.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "The language locale, e.g., 'en' for English or 'es' for Spanish.",
                    }
                },
                "required": ["locale"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_experience",
            "description": "Fetch a list of my work experiences, including companies, roles, tasks, and technologies. Use this to provide information about my work history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "The language locale, e.g., 'en' for English or 'es' for Spanish.",
                    }
                },
                "required": ["locale"],
            },
        },
    },
]
