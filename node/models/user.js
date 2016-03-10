/**
 * Created by denis on 29.02.16.
 */
module.exports = function(sequelize, DataTypes) {
  Message = sequelize.import(__dirname + '/message');
  var User = sequelize.define("User", {
    email: DataTypes.STRING,
    username: DataTypes.STRING
  }, {
    tableName: 'base_member',
    timestamps: false
  });
  User.hasMany(Message, {as: 'messages'});
  return User;
};