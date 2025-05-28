const SCFGBaseCommand = [
  { name: 'forward', zh: '向前走' },
  { name: 'back', zh: '向后走' },
  { name: 'left', zh: '向左走' },
  { name: 'right', zh: '向右走' },
  { name: 'duck', zh: '下蹲' },
  { name: 'attack', zh: '左键' },
  { name: 'attack2', zh: '右键' },
  { name: 'sprint', zh: '静步' },
  { name: 'lookatweapon', zh: '检视' },
  { name: 'turnleft', zh: '视角向左' },
  { name: 'turnright', zh: '视角向右' },
  { name: 'turnup', zh: '视角向上' },
  { name: 'turndown', zh: '视角向下' },
];


SCFGBaseCommand.forEach(cmd => {
  Blockly.Blocks[`lua_${cmd.name}`] = {
    init: function () {
      this.appendValueInput('DISTANCE')
        .setCheck('Number')
        .appendField(cmd.zh);
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setColour(230);
      this.setTooltip(`${cmd.name}(x)`);
      this.setHelpUrl('');
      const shadowDom = Blockly.utils.xml.textToDom(
        '<shadow type="math_number">' +
        '<field name="NUM">1</field>' +
        '</shadow>'
      );
      this.getInput('DISTANCE').connection.setShadowDom(shadowDom);
    }
  };
});

SCFGBaseCommand.forEach(cmd => {
  lua.luaGenerator.forBlock[`lua_${cmd.name}`] = function (block, generator) {
    var value_distance = generator.valueToCode(block, 'DISTANCE', generator.ORDER_NONE) || '1';
    var code = `${cmd.name}(` + value_distance + ')\n';
    return code;
  };
});