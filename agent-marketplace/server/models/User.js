const mongoose = require('mongoose');

const Schema = mongoose.Schema;

// User Schema
const userSchema = new Schema({
    name: { 
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true,
        unique: true // Assuming you want the email to be unique for each user
    },
    password: {
        type: String,
        required: true
    },
    agents: [{ 
        type: Schema.Types.ObjectId, // Reference to Agent documents
        ref: 'Agent' // This should match the name given to your agent model
    }]
}, 
{collection: 'users'});

module.exports = mongoose.model('User', userSchema);
