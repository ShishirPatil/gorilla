require('dotenv').config({path: '.env'});
const express = require('express');
const mongoose = require('mongoose');
const agentRoutes = require('./routes/agentRoutes'); 
const reviewRoutes = require('./routes/reviewRoutes'); 
const userRoutes = require('./routes/userRoute');
const { MongoClient } = require('mongodb');
const jwt = require('jsonwebtoken');
const User = require('./models/User'); // Adjust the path to where your user model file is located.
const bcrypt = require('bcryptjs');
const Agent = require('./models/Agent');


// Add your agents in the data array as a json object with the following schema: name, description, readme, source, skeleton Code, additional resources
const agentsData = [ 

];



const app = express();

const cors = require('cors');
app.use(cors());

// Allow all origins
app.use(cors({
    origin: '*',
    credentials: true,
    methods: "GET,HEAD,PUT,PATCH,POST,DELETE",
    allowedHeaders: "Content-Type,Authorization"
}));



app.use(express.json());
console.log(process.env.MONGODB_URI);
mongoose.connect(process.env.MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    dbName: 'agentsDB' 
})
.then(() => console.log('Connected to MongoDB'))
.catch(err => console.error('Could not connect to MongoDB:', err));


app.post('/api/login', async (req, res) => {
    const { email, password } = req.body;
    try {
        const user = await User.findOne({ email });
        if (user && await bcrypt.compare(password, user.password)) {
            
            
            const token = jwt.sign(
                { id: user._id }, // Payload
                'secret123', // Secret key, should be in your environment variables
                { expiresIn: '1h' } // Options, e.g., token expires in 1 hour
            );

           

            res.status(200).json({ 
                message: 'Login successful',
                token: token,// Send the token to the client
                name:user.name
            });
        } else {
            // Wrong credentials
            res.status(401).json({ message: 'Login failed: Incorrect email or password' });
        }
    } catch (error) {
        res.status(500).json({ message: 'Internal server error' });
    }
});

app.post('/api/register', async (req, res) => {
    try {
        const hashedPassword = await bcrypt.hash(req.body.password, 10); // 10 is the number of rounds for salting
        const user = await User.create({
            name: req.body.name,
            email: req.body.email,
            password: hashedPassword,
        });
        res.json({ status: 'ok', name:user.name});
    } catch (err) {
        res.json({ status: 'error', message: err.message });
    }
});
app.use('/api/agents', agentRoutes);

app.use('/api', userRoutes);

// Use the review routes
app.use('/api/reviews', reviewRoutes); 

console.log(process.env.PORT);

app.listen(process.env.PORT || 3000, () => {
    console.log(`Server is running on port ${process.env.PORT || 3000}`);
    initializeAgents(); // Call the function to initialize agents after server starts
}).on('error', (err) => {
    console.error('Server failed to start:', err);
});



async function initializeAgents() {
    try {
        console.log("Initializing agents...");
        for (const agent of agentsData) {
            const existingAgent = await Agent.findOne({ name: agent.name });
            if (!existingAgent) {
                await Agent.create(agent);
                console.log(`Inserted agent: ${agent.name}`);
            } else {
                console.log(`Agent already exists: ${agent.name}`);
            }
        }
    } catch (e) {
        console.error('Error inserting agents:', e);
    }
}


initializeAgents();
module.exports = app;


