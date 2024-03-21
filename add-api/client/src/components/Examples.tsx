import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { ConvertResult } from '../types/types';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import { grey, orange } from '@mui/material/colors';
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
        username: 'user2',
        apiName: 'API Two',
        urls: ['https://example.com/api3', 'https://example.com/api4'],
        urlsResults: {},
    },
    {
        username: 'user2',
        apiName: 'API Two',
        urls: ['https://example.com/api3', 'https://example.com/api4'],
        urlsResults: {},
    },
    // TODO: Add more examples
];




const containerStyles = {
    padding: '1rem',
    backgroundColor: grey[100],
    borderRadius: '12px',
};

const buttonStyles = {
    textTransform: 'none',
    minWidth: '150px',
    '&:hover': {
        backgroundColor: orange[100],
    },
};

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
        <div className="container" style={containerStyles}>
            <div className="d-flex">
                <TipsAndUpdatesIcon fontSize="small" style={{ color: orange[500] }} />
                <Typography variant="h6" component="h6" gutterBottom>
                    Examples
                </Typography>
            </div>
            <Stack direction="row" spacing={3}>
                {exampleData.map((example, index) => (
                    <Button
                        key={index}
                        variant="outlined"
                        onClick={() => handleClick(example)}
                        sx={buttonStyles}
                    >
                        {`${example.apiName}`}
                    </Button>
                ))}
            </Stack>
        </div>
    );
};

export default Examples;
