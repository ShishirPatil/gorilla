const express = require("express");
const bcryptjs = require('bcryptjs');
const User = require("../models/User");
const userRouter = express.Router();
const jwt = require("jsonwebtoken");
const auth = require("../middleware/auth");

// Signup Route
userRouter.post("/signup", async (req, res) => {
  try {
    const { email, password, confirmPassword, username } = req.body;
    if (!email || !password || !username || !confirmPassword) {
      return res.status(400).json({ msg: "Please enter all the fields" });
    }
    if (password.length < 6) {
      return res
        .status(400)
        .json({ msg: "Password should be atleast 6 characters" });
    }
    if (confirmPassword !== password) {
      return res.status(400).json({ msg: "Both the passwords dont match" });
    }
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res
        .status(400)
        .json({ msg: "User with the same email already exists" });
    }
    const hashedPassword = await bcryptjs.hash(password, 8);
    const newUser = new User({ email, password: hashedPassword, username});

    const savedUser = await newUser.save();
    res.json(savedUser);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Login Route
userRouter.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ msg: "Please enter all the fields" });
    }

    const user = await User.findOne({ email });
    if (!user) {
      return res
        .status(400)
        .send({ msg: "User with this email does not exist" });
    }

    const isMatch = await bcryptjs.compare(password, user.password);

    if (!isMatch) {
      return res.status(400).send({ msg: "Incorrect password." });
    }
    const token = jwt.sign({ id: user._id }, "passwordKey");
    res.json({ token, user: { id: user._id, username: user.name } });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

userRouter.get("/my-agents", async (req, res) => {
  try {
    // Use the ID from the authenticated user added by the auth middleware
    const email = req.query.email;

    const user = await User.findOne({ email });
    // Assuming your User model references agents by their IDs
    const userWithAgents = await user.populate("agents");
    if (!userWithAgents) {
      return res.status(404).json({ msg: "User not found" });
    }
    
    // If the user is found but has no agents
    if (userWithAgents.agents.length === 0) {
      return res.status(404).json({ user: user, msg: "No agents found for this user" });
    }

    res.json(userWithAgents.agents); // Return the user's agents
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// TO CHECK IF TOKEN IS VALID
userRouter.post("/tokenIsValid", async (req, res) => {
  try {
    const token = req.header("x-auth-token");
    if (!token) return res.json(false);
    const verified = jwt.verify(token, "passwordKey");
    if (!verified) return res.json(false);
    const user = await User.findById(verified.id);
    if (!user) return res.json(false);
    return res.json(true);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// to get the users credentials
userRouter.get("/", auth, async (req, res) => {
  const user = await User.findById(req.user);
  res.json({
    username: user.username,
    id: user._id,
  });
});

module.exports = userRouter;