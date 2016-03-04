/**
 * Created by denis on 29.02.16.
 */
module.exports = function(sequelize, DataTypes) {
  var User = sequelize.define("User", {
    email: DataTypes.STRING
  }, {
    tableName: 'base_member',
    timestamps: false
  });

  return User;
};