## Debugging

Breakpoint debugging is supported for both PyCharm and VSCode. To enable it:

1) Set-up your Python Debug Server for either [PyCharm](https://www.jetbrains.com/help/pycharm/remote-debugging-with-product.html#remote-debug-config) or [VSCode](https://code.visualstudio.com/docs/python/debugging#_command-line-debugging) and start it
2) In your script, include `bsyn.run_this_script(debug = True, port_number = <YOUR PORT NUMBER>, host = <YOUR HOST NAME>)`
3) Run the script - breakpoints should now work!

## Troubleshooting
Note that `bsyn` imports all `bpy` functionality, so you can call any `bpy` function as if you would normally.

If any issues with the Blender scripts not having the correct modules, try `bsyn.fix_blender_modules()`, or to completely reconfigure Blender, `bsyn.fix_blender_install()`. If installing from local clone, use `local=True` argument to both. If you are making changes to the local clone, use `editable=True` to install in editable mode.