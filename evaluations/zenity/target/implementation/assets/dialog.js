function run(argv) {
    const p = JSON.parse(argv[0]);
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;
    app.activate();
    const options = {buttons: p.entry || p.question ? [p.cancel, p.ok] : [p.ok], defaultButton: p.entry || p.question ? 2 : 1};
    if (p.entry || p.question) options.cancelButton = 1;
    if (p.entry) {
        options.withTitle = p.title;
        options.defaultAnswer = p.value;
    } else {
        options.message = p.text;
        if (!p.question) options.as = "informational";
    }
    try {
        const result = p.entry ? app.displayDialog(p.text, options) : app.displayAlert(p.title, options);
        return JSON.stringify([true, p.entry ? result.textReturned : ""]);
    } catch (error) {
        if (error.errorNumber !== -128) throw error;
        return JSON.stringify([false, ""]);
    }
}
