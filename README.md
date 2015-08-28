# Lazy Docker

Sometimes deploying Docker stacks can be a pain. What if they didn't have to be?

Reduce those really long commands into files you can make once and change easily. **Be lazy.**

With Lazy Docker, you only need to run `./DockerMachine.py --help` or `./DockerContainer.py --help` to see how to use it.

### Note
Lazy Docker is written for Python 3. This is usually not the default Python environment, so you'll need to be sure python3 is installed. Also, if you want to run these files directly, be sure and run `chmod +x DockerMachine.py DockerContainer.py` in this directory.

To start something like Consul, you could run something like:

`./DockerContainer.py create consul_test consul:server`

## The power of being this lazy

Say you want to run multiple Docker Machines with Consul on each one (with all of its slightly confusing configuration). First, let's set up a Docker Hub mirror.

```
./DockerMachine.py create --no-registry-mirror registry
./DockerContainer.py --machine registry registry_container registry:mirror
```
Done! Now we've got a mirror for when all of our other machines want to download something. Each of those `--command` type arguments have single letter aliases as well.

Now onto creating Consul's machines.

```
./DockerMachine.py create docker1
./DockerContainer.py -m docker1 create consul consul:first
```
Now in the config file (inside `conf.d`) called consul_server.json, change the command portion where it `join`s some kind of `{{consul}}` to the name of your machine we just made, in `{{`braces`}}`. (i.e. `{{docker1}}`)

Now run these:
```
./DockerMachine.py create docker2
./DockerContainer.py -m docker1 create consul consul:server
```
Now you have two Consul machines with a Consul container on each.

### Note
The configurations and default arguments in this CLI are very opinionated but should be fairly easy to change. Take a look either in the config files or the respective Python file you're using (towards the bottom of the files).

## Not convinced that was short enough? Want to see what it is doing?
If you're curious, devious, or all of the above, just run `export UTILS_DEBUG=true` in your command line. (To undo that, use `unset UTILS_DEBUG`)

Now run any command you want to test out! All of the commands should actually just print out the docker/docker-machine commands it would have run normally.


# Disclaimer

This is *definitely* in alpha. Feel free to use it, but don't expect it to work 100%!
