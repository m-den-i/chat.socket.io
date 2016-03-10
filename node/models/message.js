/**
 * Created by denis on 3/8/16.
 */
module.exports = function(sequelize, DataTypes) {
    return sequelize.define("Message", {
        text: DataTypes.TEXT,
        sent: DataTypes.DATE
    }, {
        tableName: 'base_message',
        timestamps: false
    });
};