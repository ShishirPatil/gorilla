const express = require('express');
const Agent = require('../models/Agent');
const User = require('../models/User'); 

const router = express.Router();

// Get all agents
router.get('/', async (req, res) => {
    try {
        const agents = await Agent.find();
        res.json(agents);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

// Get one agent by ID
router.get('/:id', async (req, res) => {
    try {
        const agent = await Agent.findById(req.params.id);
        if (!agent) return res.status(404).json({ message: 'Agent not found' });
        res.json(agent);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

router.post('/', async (req, res) => {
    const { name, description, readme, source, apiKeyRequired, skeletonCode, additionalResources, origin, email } = req.body;

    try {
        const user = await User.findOne({ email }); // Make sure to wait for the user to be found

        if (!user) {
            return res.status(401).json({ message: 'User not found' });
        }
        
        const newAgent = new Agent({
            name,
            description,
            readme,
            source,
            skeletonCode,
            additionalResources,
            origin
        });

        // Save the new agent
        const savedAgent = await newAgent.save();

        // Add the new agent's ID to the user's agents array and save the user document
        user.agents.push(savedAgent._id);
        await user.save();

        res.status(201).json(savedAgent);
    } catch (error) {
        res.status(400).json({ message: error.message });
    }
});

router.get('/stats', async (req, res) => {
    try {
      const totalAgents = await Agent.countDocuments();
      // Assuming 'status' field exists and 'running' is the status for active agents
      const runningAgents = await Agent.countDocuments({ status: 'running' });
      
      res.json({
        totalAgents,
        runningAgents
      });
    } catch (error) {
      res.status(500).json({ message: "Error fetching agent stats", error: error.message });
    }
  });
  




module.exports = router;