const jwt = require("jsonwebtoken");

const auth = async (req, res, next) => {
  try {
    console.log(process.env.JWT_SECRET)
    let token = req.header("Authorization");
    if (!token) {
      return res.status(401).json({ msg: "No auth token, access denied" });
    }
    
    // Check if the token follows the "Bearer [token]" format
    if (token.startsWith("Bearer ")) {
      // Remove "Bearer " to get the actual token
      token = token.slice(7, token.length);
    }

    const verified = jwt.verify(token, "passwordKey");
    if (!verified) {
      return res.status(401).json({ msg: "Token verification failed, authorization denied" });
    }
    req.user = verified.id;
    next();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

module.exports = auth;
