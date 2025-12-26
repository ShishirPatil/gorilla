import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { ConvertResult } from '../types/types';
import Stack from '@mui/material/Stack';
interface Example {
    username: string;
    apiName: string;
    urls: string[];
    urlsResults: ConvertResult;
}

const exampleData: Example[] = [
    {
        username: 'Amokhalad',
        apiName: 'Stripe Files API',
        urls: ['https://docs.stripe.com/api/files'],
        urlsResults: {
            "https://docs.stripe.com/api/files": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "Create File",
                        "api_call": "stripe.File.create(file='@/path/to/a/file.jpg', purpose='dispute_evidence')",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "file",
                                "purpose"
                            ]
                        ],
                        "functionality": "Upload a file to Stripe",
                        "env_requirements": null,
                        "example_code": "curl https://files.stripe.com/v1/files \\ -u sk_test_4eC39Hq...arjtT1zdp7dcsk_test_4eC39HqLyjWDarjtT1zdp7dc: \\ -F purpose=dispute_evidence \\ -F file=\"@/path/to/a/file.jpg\"",
                        "meta_data": null,
                        "Questions": [
                            "I need to upload a file to Stripe for dispute evidence. How can I achieve this?"
                        ]
                    },
                    {
                        "user_name": "Amokhalad",
                        "api_name": "Retrieve File",
                        "api_call": "stripe.File.retrieve(id='file_1Mr4LDLkdIwHu7ixFCz0dZiH')",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "id"
                            ]
                        ],
                        "functionality": "Retrieve details of an existing file",
                        "env_requirements": null,
                        "example_code": "curl https://api.stripe.com/v1/files/@/path/to/a/file.png \\ -u \"sk_test_4eC39Hq...arjtT1zdp7dcsk_test_4eC39HqLyjWDarjtT1zdp7dc:\"",
                        "meta_data": null,
                        "Questions": [
                            "I want to retrieve details of a specific file. How can I do that?"
                        ]
                    },
                    {
                        "user_name": "Amokhalad",
                        "api_name": "List Files",
                        "api_call": "stripe.File.list(limit=3)",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "limit"
                            ]
                        ],
                        "functionality": "List all files accessible to the account",
                        "env_requirements": null,
                        "example_code": "curl -G https://api.stripe.com/v1/files \\ -u \"sk_test_4eC39Hq...arjtT1zdp7dcsk_test_4eC39HqLyjWDarjtT1zdp7dc:\" \\ -d limit=3",
                        "meta_data": null,
                        "Questions": [
                            "How can I list all the files accessible to my account?"
                        ]
                    }
                ]
            }
        },
    },
    {
        username: 'your-github-username',
        apiName: 'Torch.CPU',
        urls: ['https://pytorch.org/docs/stable/generated/torch.cpu.current_device.html#torch.cpu.current_device', 'https://pytorch.org/docs/stable/generated/torch.cpu.current_stream.html#torch.cpu.current_stream', "https://pytorch.org/docs/stable/generated/torch.cpu.is_available.html#torch.cpu.is_available", "https://pytorch.org/docs/stable/generated/torch.cpu.synchronize.html#torch.cpu.synchronize"],
        urlsResults: {
            "https://pytorch.org/docs/stable/generated/torch.cpu.current_device.html#torch.cpu.current_device": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "torch.cpu.current_device",
                        "api_call": "torch.cpu.current_device()",
                        "api_version": null,
                        "api_arguments": [],
                        "functionality": "Returns current device for cpu. Always 'cpu'. This function only exists to facilitate device-agnostic code",
                        "env_requirements": null,
                        "example_code": "import torch\ncurrent_device = torch.cpu.current_device()",
                        "meta_data": null,
                        "Questions": [
                            "How can I determine the current device for CPU in Torch?"
                        ]
                    }
                ]
            },
            "https://pytorch.org/docs/stable/generated/torch.cpu.current_stream.html#torch.cpu.current_stream": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "torch.cpu.current_stream",
                        "api_call": "torch.cuda.current_stream(device=None)",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "device"
                            ]
                        ],
                        "functionality": "Returns the currently selected stream for a given device.",
                        "env_requirements": null,
                        "example_code": "import torch\nstream = torch.cuda.current_stream()\nprint(stream)",
                        "meta_data": null,
                        "Questions": [
                            "I am working on a deep learning project and need to manage streams for different devices. How can I get the currently selected stream for a specific device?"
                        ]
                    }
                ]
            },
            "https://pytorch.org/docs/stable/generated/torch.cpu.is_available.html#torch.cpu.is_available": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "torch.cpu.is_available",
                        "api_call": "torch.cpu.is_available()",
                        "api_version": null,
                        "api_arguments": [],
                        "functionality": "Returns a bool indicating if CPU is currently available.",
                        "env_requirements": null,
                        "example_code": "import torch\n\n# Check if CPU is available\ncpu_available = torch.cpu.is_available()\nprint(cpu_available)",
                        "meta_data": null,
                        "Questions": [
                            "I am developing a machine learning model and want to check if CPU is available for training."
                        ]
                    }
                ]
            },
            "https://pytorch.org/docs/stable/generated/torch.cpu.synchronize.html#torch.cpu.synchronize": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "torch.cpu.synchronize",
                        "api_call": "torch.cuda.synchronize(device='cpu')",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "device"
                            ]
                        ],
                        "functionality": "Waits for all kernels in all streams on the CPU device to complete.",
                        "env_requirements": null,
                        "example_code": "import torch\ntorch.cuda.synchronize(device='cpu')",
                        "meta_data": null,
                        "Questions": [
                            "I have a machine learning model running on the CPU device. How can I ensure that all kernels in all streams have completed before proceeding to the next step?"
                        ]
                    }
                ]
            }
        },
    },
    {
        username: 'your-github-username',
        apiName: 'Gmail API - Sending Mail',
        urls: ["https://developers.google.com/gmail/api/guides/sending"],
        urlsResults: {
            "https://developers.google.com/gmail/api/guides/sending": {
                "status": "success",
                "data": [
                    {
                        "user_name": "Amokhalad",
                        "api_name": "Gmail API - Send Email Directly",
                        "api_call": "service.users().messages().send(userId='me', body=message).execute()",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "userId",
                                "me"
                            ],
                            [
                                "body",
                                "message"
                            ]
                        ],
                        "functionality": "Send email directly using the Gmail API",
                        "env_requirements": [
                            "google-auth",
                            "google-api-python-client"
                        ],
                        "example_code": "import google.auth\nfrom googleapiclient.discovery import build\n\ncreds, _ = google.auth.default()\nservice = build('gmail', 'v1', credentials=creds)\nmessage = {'raw': 'base64_encoded_message_here'}\nresult = service.users().messages().send(userId='me', body=message).execute()",
                        "meta_data": null,
                        "Questions": [
                            "I want to send automated emails from my application. How can I achieve this using the Gmail API?"
                        ]
                    },
                    {
                        "user_name": "Amokhalad",
                        "api_name": "Gmail API - Send Email from Draft",
                        "api_call": "service.users().drafts().send(userId='me', body=message).execute()",
                        "api_version": null,
                        "api_arguments": [
                            [
                                "userId",
                                "me"
                            ],
                            [
                                "body",
                                "message"
                            ]
                        ],
                        "functionality": "Send email from a draft using the Gmail API",
                        "env_requirements": [
                            "google-auth",
                            "google-api-python-client"
                        ],
                        "example_code": "import google.auth\nfrom googleapiclient.discovery import build\n\ncreds, _ = google.auth.default()\nservice = build('gmail', 'v1', credentials=creds)\nmessage = {'raw': 'base64_encoded_message_here'}\nresult = service.users().drafts().send(userId='me', body=message).execute()",
                        "meta_data": null,
                        "Questions": [
                            "How can I send an email that was saved as a draft using the Gmail API?"
                        ]
                    }
                ]
            }
        },
    },
    // TODO: Add more examples
];

const Examples: React.FC = () => {
    const { setUsername, setApiName, setUrls, setUrlsResults } = useDashboard();

    // Handles clicking on an example, setting the context with its values
    const handleClick = (example: Example) => {
        setUsername(example.username);
        setApiName(example.apiName);
        setUrls(example.urls);
        setUrlsResults(example.urlsResults);
    };

    return (
        <div className="container examples-container">
            <h5>Examples</h5>
            <Stack direction="row" spacing={3}>
                {exampleData.map((example, index) => (
                    <button
                        type="button"
                        className="btn btn-link btn-db btn-ex"
                        key={index}
                        onClick={() => handleClick(example)}
                    >
                        {example.apiName}
                    </button>
                ))}
            </Stack>
        </div >
    );
};

export default Examples;
