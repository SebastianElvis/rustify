ObjC.import('stdio');
ObjC.import('stdlib');
var app = Application.currentApplication();
app.includeStandardAdditions = true;
app.activate();
try {
    var res = app[p.operation](p.text, p.options);
} catch (error) {
    if (error.errorNumber === -128) $.exit(1);
    $.dprintf(2, error);
    $.exit(-1);
}
if (res.gaveUp) $.exit(5);
res.textReturned;
