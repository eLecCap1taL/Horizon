//sleep

Blockly.Blocks[`lua_sleep`] = {
    init: function () {
        this.appendValueInput('DISTANCE')
            .setCheck('Number')
            .appendField('延时(tick)');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip(`sleep(x)`);
        this.setHelpUrl('');
        const shadowDom = Blockly.utils.xml.textToDom(
            '<shadow type="math_number">' +
            '<field name="NUM">1</field>' +
            '</shadow>'
        );
        this.getInput('DISTANCE').connection.setShadowDom(shadowDom);
    }
};

lua.luaGenerator.forBlock[`lua_sleep`] = function (block, generator) {
    var value_distance = generator.valueToCode(block, 'DISTANCE', generator.ORDER_NONE) || '1';
    var code = `sleep(` + value_distance + ')\n';
    return code;
};