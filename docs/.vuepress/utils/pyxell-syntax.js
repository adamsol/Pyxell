
module.exports = {
    atom: /\b(?:true|false|null|this|super|default)\b/,
    keyword: /\b(?:abstract|and|as|break|by|class|constructor|continue|def|destructor|do|elif|else|extern|for|func|hiding|if|in|is|lambda|not|only|or|print|return|skip|super|until|use|while|yield)\b/,
    variable_name: /\b[a-z_][\w']*/,  // so that apostrophes in variable names are handled properly
    type_name: /\b[A-Z][\w']*/,
    number: /(?:0b[01_]+|0o[0-7_]+|0x[\da-fA-F_]+|\d[\d_]*(?:(\.[\d_]+)?(?:[eE][-+]?[\d_]+|f)?|r)?)\b/,
    string: /"(?:[^\\"]|\\(?:["\\abfnrt]|x[0-9a-fA-F]+))*(?:"|$)|'(?:[^\\']|\\(?:['\\abfnrt]|x[0-9a-fA-F]+))?(?:'|$)/,
};
