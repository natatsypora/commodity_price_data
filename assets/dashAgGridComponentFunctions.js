/*The function to display the graph component*/

var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DCC_GraphClickData = function (props) {
    return React.createElement(window.dash_core_components.Graph, {
        figure: props.value,
        style: {height: '100%'},
        config: {displayModeBar: false},
    });
};

