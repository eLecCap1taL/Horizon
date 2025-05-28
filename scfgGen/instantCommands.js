const SCFGInstantCommand = [
  { name: 'jump', zh: '跳跃' },
  { name: 'jumpbug', zh: 'JumpBug' }
];


SCFGInstantCommand.forEach(cmd => {
  Blockly.Blocks[`lua_${cmd.name}`] = {
    init: function () {
      this.appendDummyInput()
        .appendField(`${cmd.zh}`);
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setTooltip(`${cmd.name}()`);
      this.setHelpUrl('');
      this.setColour(225);
    }
  };
});

SCFGInstantCommand.forEach(cmd => {
  lua.luaGenerator.forBlock[`lua_${cmd.name}`] = function () {
    return `${cmd.name}()\n`;
  };
});