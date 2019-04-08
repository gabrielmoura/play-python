#!/usr/bin/env python

import socket, logging, sys, re, argparse, configparser


def help(irc, name, topic=''):
    # set default help message to blank.
    message = ''
    # if no help topic is specified, send general help message about the bot.
    if topic == '':
        message = "Hi! I am an irc bot"
    # if a help message is specified, let the user know it's not coded yet.
    else:
        message = "Feature not yet implemented, sorry. Please see the main help (message me with \'.help\')"
    # logging.debug(topic)
    # send help message in whisper to user.
    whisper(irc, message, name)


def checksend(irc, name, orig, new, pattern=''):
    # if the original message and new message are the same then do nothing.
    if orig == new:
        whisper(irc, "No text would be changed.", name)
        return
    # if the find used very broad wildcards then do nothing. May need to add more or think of new method for this.
    if pattern in {'\\s', '\\S', '\\D', '\\W', '\\w'}:
        whisper(irc,
                "Wildcard(s) not allowed because they are too broad. If you meant to seach plaintext use 's/[find]/[replace]' or delimit the wildcard (like s|\\\\s|!s",
                name)
        return
    # if new message would be over 200 characters then do not send.
    if len(new) > 200:
        whisper(irc, "Resulting message is too long (200 char max)", name)
        return
    # if new message is empty string do not send.
    if len(new) == 0:
        whisper(irc, "Replace resulted in empty messge. Nothing to send", name)
        return
    # if message isn't caught by one of the checks, send to channel and log the message.
    message = "Correction, <" + name + ">: " + new
    sendmsg(irc, message.strip('\r\n'))
    logging.info(name + new)


# Regex Find/Replace
def regex(msg):
    # detect if there are fewer than 2 '|' in the message. If so, not a valid find/replace pair, do nothing.
    if msg.count('|') < 2:
        print("Not enough arguments")
        return
    # get the text between the first and last '|' as the 'find portion
    sedtest = msg.split('|', 1)[1].rsplit('|', 1)[0]
    # if there is no text between the first and last '|' (as in 's||somethin') do nothing because there is nothing to find.
    if sedtest == '':
        print("Nothing to find")
        return
    # set the replace text to everything after the last '|'
    sreplace = msg.split('|', 1)[1].rsplit('|', 1)[1]
    # set the default replaced text to a known, default value
    replaced = ".__not found__."
    # escape any '*' wildcards as they are too broad so assume they are literal. Needs testing for '\*' searches.
    if (sedtest.find("*") != -1):
        findme = sedtest.replace('*', '\*')
    # if find is a single character, escape it because it any regex would be too broad.
    elif len(sedtest) == 1:
        findme = re.escape(sedtest)
    else:
        # if neither of the other two are true, set the find string.
        findme = sedtest
    try:
        # set the pattern to find
        pattern = re.compile("(%s)" % findme)
    except Exception:
        # if there is an error, escape the find string and try again. --Needs further testing.
        findme = re.escape(findme)
        pattern = re.compile("(%s)" % findme)
        pass
    # Read in the chat log
    with open("ircchat.log", "rb") as ircchat:
        content = ircchat.readlines()
    # set default replaced text, username, and found string
    repltext = ('', 0)
    name = ''
    found = ''
    # loop through chat log
    for i in content:
        try:
            # set text equal to just the message, no username.
            text = i.split(":", 1)[1]
            # search the text for regex pattern, if found, set found equal to the text and replace it with replace string. Set name equal to the username of found message.
            if pattern.search(text):
                text = text.strip('\n\r')
                found = text
                repltext = re.subn(pattern, sreplace, text)
                name = i.split(":", 1)[0]
        # ignore errors and continue. --Needs further testing
        except Exception:
            print('error in search')
            pass
    # if the regex found more than 10 matches, assume it was too broad and let the user know. --Change to whisper?
    if repltext[1] > 10:
        sendmsg("Too many matches, refine your correction")
        return
    # set replaced string equal to just the new message and strip newlines, then send to checksend for verification before sending to channel.
    replaced = repltext[0]
    replaced = replaced.strip('\n\r')
    checksend(name, found, replaced, findme)


# Plaintext Find/Replace.
def sed(msg):
    # detect if there are fewer than 2 '/' in the message. If so, not a valid find/replace pair, do nothing.
    if msg.count('/') < 2:
        print("not enough arguments")
        return
    # get the text between the first and last '/' as the 'find' portion
    sedtest = msg.split('/', 1)[1].rsplit('/', 1)[0]
    # if there is no text between the first and last '/' (as in 's//somethin') do nothing because there is nothing to find.
    if sedtest == '':
        print("Nothing to find")
        return
    # set the replace text to everything after the last '/'
    sreplace = msg.split('/', 1)[1].rsplit('/', 1)[1]
    # set the default replaced text to a known, default value
    replaced = ".__not found__."
    # read in the chat log file
    with open("ircchat.log", "rb") as ircchat:
        content = ircchat.readlines()
        # loop through the chat log and search through the messages for a match to the 'find' string. Ignore any errors -- to be fixed.
    for i in content:
        try:
            if i.split(':', 1)[1].find(sedtest) != -1:
                replaced = i
        except Exception:
            pass
    # if the default replaced text was not changed, no matches were found in the log, do nothing.
    if replaced == ".__not found__.":
        print("not found")
        return
    else:
        # if the default replaced text was found, perform a replace on the text, strip any newlines, and send to checksend method for verification before sending to channel.
        name = replaced.split(':', 1)[0]
        replaced = replaced.split(':', 1)[1].replace(sedtest, sreplace)
        replaced = replaced.strip('\n\r')
        checksend(name, sedtest, replaced)


def joinchan(irc, chan):  # join channel(s).
    irc.send(bytes("JOIN " + chan + "\n", "UTF-8"))
    ircmsg = ""
    while ircmsg.find("End of /NAMES list.") == -1:
        ircmsg = irc.recv(2048).decode("UTF-8")
        ircmsg = ircmsg.strip('\n\r')
        logging.debug(ircmsg)


def ping(ircmsg, irc):  # respond to server Pings.
    if ircmsg.find("PING :") != -1:
        irc.send(bytes("PONG :pingis\n", "UTF-8"))
    else:
        irc.send(bytes("PONG :pingis\n", "UTF-8"))


def sendmsg(irc, msg, channel):  # sends messages to the target.
    irc.send(bytes("PRIVMSG " + channel + " :" + msg + "\n", "UTF-8"))


def whisper(irc, msg, user):  # whisper a user

    irc.send(bytes("PRIVMSG " + user + ' :' + msg.strip('\n\r'), "UTF-8"))


def command(command, message):
    n = len(command)
    com = message[:n]
    par = message[n:]
    return (com, par)


def ask_user_for(something):
    'Prompts user for data'
    try:
        return input('{} not given. Please provide or press Control C to'
                     ' quit: '.format(something))
    except KeyboardInterrupt:
        sys.exit(0)


def setup():
    'Parses options from commandline and optionally the config file'
    args = parse_args()
    if not args.conf:
        args.conf = 'ignore'

    return tuple(ask_user_for(i[0].title()) if not i[1] else i[1]
                 for i in args._get_kwargs())


def parse_args():
    'Recebe os argumentos'
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument('-f', '--conf', dest='conf', metavar='FILE',
                             help='Location of config file', default='./bot.conf')
    args, remaining_args = conf_parser.parse_known_args()
    defaults = {'botnick': '',
                'server': '',
                'channel': '',
                'admin': '',
                'loglevel': 5}
    if args.conf:
        config = configparser.ConfigParser()
        config.read(args.conf)
        try:
            defaults = dict(config.items('bot'))
        except configparser.NoSectionError:
            print('Bad configuration file', file=sys.stderr)

    parser = argparse.ArgumentParser(parents=[conf_parser],
                                     description='Download files from xdcc '
                                                 'bot based on filename.')
    parser.set_defaults(**defaults)

    # Output verbosity options.
    parser.add_argument('-q', '--quiet', help='set logging to ERROR',
                        action='store_const', dest='loglevel',
                        const=logging.ERROR, default=logging.INFO)

    parser.add_argument('-d', '--debug', help='set logging to DEBUG',
                        action='store_const', dest='loglevel',
                        const=logging.DEBUG, default=logging.INFO)

    parser.add_argument('-v', '--verbose', help='set logging to COMM',
                        action='store_const', dest='loglevel',
                        const=5, default=logging.INFO)

    parser.add_argument("-n", "--nick", dest="botnick", help="O Nick do bot")
    parser.add_argument("-s", "--server", dest="server", help="Servidor")
    parser.add_argument("-c", "--channel", dest="channel", help="Canal")
    parser.add_argument("-a", "--admin", dest="admin", help="Nick do administrador")

    args = parser.parse_args(remaining_args)

    return args


def login(irc, server, botnick, **kwargs):
    'Inicia sessão'
    # ircmsg = ircsock.recv(2048).decode("UTF-8")
    try:
        irc.connect((server, 6667))
    except socket.gaierror:
        logging.error('Bad server name')
        sys.exit()
    except socket.timeout:
        logging.error('Time out')

    # Here we connect to the server using the port 6667
    irc.send(bytes("USER " + botnick + " " + botnick + " " + botnick + " " + botnick + "\n",
                   "UTF-8"))  # We are basically filling out a form with this line and saying to set all the fields to the bot nickname.
    irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))  # assign the nick to the bot
    irc.settimeout(2)

    while True:  # https://github.com/mac-reid/lazydcc/issues/1
        try:
            ircmsg = irc.recv(4096).decode("UTF-8")
            ircmsg = ircmsg.strip('\n\r')
        except socket.timeout:
            # logging.error('Time Out')
            break

        if ircmsg.startswith('PING'):
            ping(ircmsg, irc)

        if ircmsg.find("Nickname is already in use") != -1:
            botnick += '_'
            irc.send(bytes('NICK ' + botnick + '\n', "UTF-8"))
    irc.settimeout(None)


def outchan(irc, channel):
    'Abandona o canal especificado'
    irc.send(bytes("PART " + channel + "\r\n", "UTF-8"))


def leave_irc(irc):
    'Sends a quit command to the server and exits'
    irc.send(bytes('QUIT :bye', "UTF-8"))
    sys.exit(0)


def is_admin(admins, name):
    if name.lower() in admins:
        return True


def start():
    'Inicia o Bot'
    admin, botnick, channel, conf_dir, loglevel, server = setup()

    logging.basicConfig(level=loglevel,
                        format='%(levelname)-8s %(message)s')
    try:
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        login(irc, server, botnick)
    except KeyboardInterrupt:
        logging.error('Interrompido manualmente')
        # sys.exit(0)

    # login(irc, server, botnick)
    # Entra no canal e mostra informações
    joinchan(irc, channel)
    while 1:
        try:
            ircmsg = irc.recv(2048).decode("UTF-8")
        except KeyboardInterrupt:
            logging.error('Interrompido Manualmente')
            sys.exit()

        ircmsg = ircmsg.strip('\n\r')
        logging.debug(ircmsg)

        ping(ircmsg, irc)

        # Se for uma mensagem para o canal
        if ircmsg.find("PRIVMSG " + channel) != -1:
            name = ircmsg.split('!', 1)[0][1:]
            message = ircmsg.split('PRIVMSG ' + channel, 1)[1].split(':', 1)[1]

        # Se for uma mensagem privada para o bot
        if ircmsg.find("PRIVMSG " + botnick) != -1:
            name = ircmsg.split('!', 1)[0][1:]
            message = ircmsg.split('PRIVMSG ' + botnick, 1)[1].split(':', 1)[1]

            if message[:2] == 's|':
                regex(message)
            elif message[:2] == 's/':
                sed(message)
            elif message[:5] == '.help':
                help(irc, name, message[5:])
            else:

                # Quando comando não presente
                if len(name) < 17:
                    logging.info(name + ' : ' + message)
                    whisper(irc, "Iam a Bot" + '\r\n', name)

                    # Comando para desativar o bot
                if is_admin(admin, name) and message[:5 + len(botnick)] == "gtfo {}".format(
                        botnick):
                    # whisper(irc, "Oh...okay..." + '\r\n', admin)
                    leave_irc(irc)
                    sys.exit()


if __name__ == '__main__':
    start()
