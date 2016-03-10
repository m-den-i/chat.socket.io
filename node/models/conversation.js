/**
 * Created by denis on 3/8/16.
 */
module.exports = function(sequelize, DataTypes) {
  User = sequelize.import(__dirname + '/user');
  Message = sequelize.import(__dirname + '/message');
  var Conversation = sequelize.define("Conversation", {
    name: DataTypes.STRING
  }, {
    tableName: 'base_conversation',
    timestamps: false
  });
  Conversation.hasMany(User, {as: 'members'});
  Conversation.hasMany(Message, {as: 'messages'});
  return Conversation;
};