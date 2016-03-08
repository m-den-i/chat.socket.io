/**
 * Created by denis on 3/8/16.
 */
module.exports = function(sequelize, DataTypes) {
  var Token = sequelize.define("Token", {
    key: DataTypes.STRING,
    user_id: DataTypes.INTEGER,
    created: DataTypes.DATE,
    expire_in: DataTypes.DATE
  }, {
    tableName: 'drf_secure_token_token',
    timestamps: false
  });
  return Token;
};