from flask import *
from flask_socketio import SocketIO, emit, send, join_room, leave_room, rooms
import account_api
import api
import sys, os, json, time
from db.mysql import Connection
from hashlib import md5
from datetime import datetime
from sexy_assassin import GracefulKiller
from threading import Thread

GracefulKiller()


app = Flask(__name__)

app.secret_key = b"JIL"

sock = SocketIO( app )

@app.errorhandler(404)
def _404(err):
    return redirect( url_for('login') )

@app.route( "/login", methods = ['POST', 'GET'] )
def login():
    if ( request.method == "POST" ):
        email = request.form['email']
        pwd = request.form['pwd']
        obj = account_api.User()
        res = obj.login( email, pwd )
        if ( res == False ):
            flash( "Authentication error.", "danger" )
            return redirect( url_for( 'login' ) )
        session['uid'] = res[0]
        session['name'] = res[1]
        session['email'] = res[2]
        session['pwd'] = pwd
        session['bio'] = res[4]
        session['dfe'] = res[5]
        session['settings'] = api.load_settings( res[0] )
        return redirect( url_for( 'home' ) )
        # return redirect( url_for( 'login' ) )
    else:
        if ( 'uid' in session ):
            return redirect( url_for( 'home' ) )
    return render_template( "sign-in.html" )

@app.route("/cdn/pp/<uid>", methods = ['GET'])
def render_pp(uid):
    if ( f'{uid}.jpg' in os.listdir('pp') ):
        return send_from_directory( "pp", f"{uid}.jpg" )
    return redirect( url_for( 'static', filename = "profile.jpg" ) )

@app.route( "/sign-up", methods = ['POST', 'GET'] )
def signup():
    if ( request.method == 'POST' ):
        fname = request.form['fname'].lower().capitalize()
        lname = request.form['lname'].lower().capitalize()
        name = f"{fname} {lname}"
        email = request.form['email']
        pwd = request.form['pwd']
        obj = account_api.User()
        res = obj.create( name, email, pwd )
        if (res == -2):
            flash( "Your email is taken", "warning" ) 
            return redirect( url_for( "signup" ) )
        else:
            flash( "Your account has been created successfully.", "success" )
        return redirect( url_for( 'login' ) )
    return render_template( "sign-up.html" )


@app.route("/edit/usr", methods = ['POST'])
def edit_usr():
    if ( 'uid' not in session ):
        abort(404)
    cred = dict(request.form)
    cred['name'] = f"{cred.pop('fname')} {cred.pop('lname')}"
    obj = account_api.User()
    for i in cred:
        if ( session[i] == cred[i] ):
            continue
        res = obj.ChangeAttr( i, cred[ i ], session['uid'] )
        if ( res == True ):
            session[ i ] = cred[i]
        elif ( res == -2 ):
            flash( f"Could not change your {i} because its been taken by someone else", "warning" )
        else:
            flash( f"Could not change {i} for some reason", "warning" )
    return redirect( url_for( "home" ) )

@app.route( "/edit-setting-<ind>", methods = ['POST'] )
def edit_setting(ind):
    ind = int(ind)
    if ( 'uid' not in session ):
        return redirect( url_for( 'login' ) )
    uid = session['uid']
    val = 1 - session['settings'][ ind ]
    if ( api.change_settings( uid, ind = ind, val = val ) ):
        session['settings'] = api.load_settings(uid)
        return jsonify(True)
    return jsonify(False)

@app.route("/update-avatar", methods = ['POST'])
def update_avatar():
    avt = request.files['file']
    os.chdir("pp")
    if ( f"{session['uid']}.jpg" in os.listdir() ):
        os.remove( f"{session['uid']}.jpg" )
    avt.save( f"{session['uid']}.jpg" )
    # print("saved")
    # account_api.User.push_avt(session['uid'], fn)
    os.chdir('..')
    session['uid'] = session['uid']
    # return redirect( url_for('home') )
    return url_for('render_pp', uid = session['uid'] )

@app.route("/reset-password", methods = ['GET', 'POST'])
def reset_pwd():
    if ( request.method == 'POST' ):
        email = request.form['email']
        new_pass = api.gen_pass()
        try:
            uid = api.fetch_uid( email )
        except:
            flash( "Email is not a Neighborhood user0", 'danger' )
            return redirect( url_for( "reset_pwd" ) )
        obj = account_api.User()
        if not ( obj.ChangeAttr( "pwd", new_pass, uid ) ):
            flash( "That didnt work. please try again later0", "danger" )
            return redirect( url_for( "reset_pwd" ) )
        else:
            msg = f"Hi your neighborhood password has been successfully changed to {new_pass}"
            # send_simple_message( msg, "CONTRACT password reset", email )
            t = Thread( target = send_simple_message, args = (msg, "Neighborhood password reset", email) )
            t.start()
            # print(f"\n\n\n\n{new_pass}\n\n\n\n")
            flash( "Password has been reset successfully1", "success" )
            flash( "You'll recieve a new password in your mailbox1", "warning" )
        return redirect( url_for('login') )
    return render_template( "html/reset-pwd.html" )


@app.route("/logout")
def logout():
    pops = [ i for i in session ]
    for i in pops:
        session.pop(i)
    return redirect( url_for( 'login' ) )

@app.route("/home")
def home():
    if 'uid' not in session:
        return redirect( url_for( 'login' ) )
    session['salt'] = int(time.time())
    friends = api.Friend.fetch_friends( session['uid'] )
    f_requests = api.fetch_friend_request( session['uid'] )
    return render_template( "home.html", friends = friends, f_requests = f_requests, len = len )

@app.route("/chat/<tpuid>")
def chats(tpuid):
    if 'uid' not in session:
        abort( 501 )
    obj = api.Messenger(session['uid'])
    thread = obj.fetch_msg( tpuid, fil = session['settings'][0] )
    try:
        r_id = api.FriendRequest.fetch_id( session['uid'], tpuid )
    except:
        abort(501)
    state = api.FriendRequest.is_accepted( session['uid'], tpuid )
    if ( state != True ):
        # print(state)
        if (state == 501):
            redirect( url_for( 'display_profile', key = 0, tpuid = tpuid ) )
        abort(Response("Chat not found"))
    online = api.is_online( tpuid, obj.db )
    return render_template( "chat.html", name = api.fetchName(tpuid), thread = thread, tpuid = tpuid, r_id = r_id, is_online = online )

@app.route( "/friend-request/<tpuid>", methods = ['GET', 'POST', 'DELETE'] )
def friend_request( tpuid ):
    if 'uid' not in session:
        abort(501)
    _id = api.FriendRequest.fetch_id( session['uid'], tpuid )
    if ( _id == None ):
        abort(501)
    state = api.FriendRequest.is_accepted( session['uid'], tpuid )
    if ( state != False ):
        abort(501)

    if ( request.method == 'POST' ):
        obj = api.FriendRequest( _id, session['uid'] )
        if (obj.accept(  )):
            sock.emit(
                "new-friend", {
                'msg': f"{session['name']} Just accepted your friend request", 
                'uid': tpuid,
                'tpuid': session['uid']
                }, 
                broadcast = True
            )
            return redirect( url_for('chats', tpuid = tpuid ) )


    elif ( request.method == 'DELETE' ):
        obj = api.FriendRequest( _id, session['uid'] )
        if ( obj.delete() ):
            return redirect( url_for( 'display_profile', tpuid = tpuid, key = 0 ) )

    inf = account_api.info( tpuid, Connection() )
    info = { 'uid': inf[0], 'name': inf[1], 'bio': inf[4] }

    return render_template( "request.html", info = info )

@app.route('/delete-fr/<tpuid>', methods = ['POST'])
def delete_fr(tpuid):
    # print( f"{tpuid}" )
    if 'uid' not in session:
        abort(501)
    _id = api.FriendRequest.fetch_id( session['uid'], tpuid )
    if ( _id == None ):
        abort(501)
    obj = api.FriendRequest( _id, session['uid'] )
    if ( obj.delete() ):
        api.Notifications.super_see( session['uid'], f"f{tpuid}" )
        sock.emit( 'push', {
            'uid': tpuid,
            'tpuid': session['uid'],
            'type': 'delete',
            'msg': f"{session['name']} canceled the pending homie request"
            }, broadcast = True)
        return redirect( url_for( 'display_profile', tpuid = tpuid, key = 0 ) )
    return redirect( url_for( 'friend_request', tpuid = tpuid ) )

@app.route( '/friends' )
def friends_pipe():
    if ('uid' not in session):
        abort(501)
    fr = api.Friend.fetch_friends( session['uid'] )
    return render_template( 'friends.html', friends = fr )


@app.route("/display-profile/<tpuid>/<key>")
def display_profile( tpuid, key ):
    if 'uid' not in session:
        abort(501)
    inf = account_api.info( tpuid, Connection() )
    info = { 'uid': inf[0], 'name': inf[1], 'bio': inf[4] }
    uid = session['uid']
    vsob = api.FriendRequest.VsOb(uid, tpuid)
    if ( int(key) == 0 ):
        if ( vsob == -11 ):
            return redirect( url_for('friend_request', tpuid = tpuid) )
        elif ( vsob == -3 ):
            return redirect( url_for( 'chats', tpuid = tpuid ) )
    return render_template( "view-profile.html", info = info, vsob = vsob )

@app.route( "/delete-friend/<tpuid>", methods = ['POST'] )
def delete_friend(tpuid):
    if 'uid' not in session:
        abort(501)
    _id = api.Friend.fetch_id( session['uid'], tpuid )
    obj = api.Friend( _id, session['uid'] )
    if not ( obj.delete() ):
        abort(500)
    sock.emit( 'push', {
        'uid': tpuid,
        'tpuid': session['uid'],
        'type': 'delete',
        'msg': f"You and {session['name']} have stopped being homies"
        }, broadcast = True)
    return redirect( url_for('display_profile', tpuid = tpuid, key = 0) )

@app.route( '/fr-send/<tpuid>' )
def fr_send(tpuid):
    if 'uid' not in session:
        abort(Response("Permission denied. Login first"))

    obj = api.Notifications( tpuid )
    obj_2 = api.Friend.send( session['uid'], tpuid )

    if ( obj_2 == True ):

        res = obj.send( f"{session['name']} wants to be your homie", f"f{session['uid']}" )

        if ( res ):
            html = render_template( 'notification.html', notification = obj.fetch()[-1] )
            sock.emit( 'fr-send', {
                'tpuid': tpuid, 
                'html': html,
                'uid': session['uid'],
                'msg': f"{session['name']} sent you a homie request"}, broadcast = True )

        return redirect( url_for('display_profile', key = 0, tpuid = tpuid) )

    elif ( obj_2 == -1 ):
        sock.emit( 'spit', "Homie request already sent" )
    elif ( obj_2 == -2 ):
        sock.emit( 'spit', "You are already homies" )

    print( "That was weird @fr_send" )
    return redirect( url_for('display_profile', key = 0, tpuid = tpuid) )

@app.route("/.well-known/")
def assetlinks():
    return send_from_directory( "static", "assetlinks.json" )

@sock.on( 'connect' )
def connect():
    if 'uid' not in session:
        abort(501)
    obj = account_api.User().ChangeAttr( 'active', 1, session['uid'] )
    emit( "active", {'uid': session['uid']}, broadcast = True )

@sock.on( 'disconnect' )
def disconnect():
    if 'uid' not in session:
        abort(501)
    obj = account_api.User().ChangeAttr( 'active', 0, session['uid'] )
    emit( "inactive", {'uid': session['uid']}, broadcast = True )


@sock.on('neighbors')
def neighbors(data):
    if ( 'loadPrev' in data ):
        # print("offline computation in progress")
        data = session['dfe']
    n = api.compute_neighbors( data, session['uid'], babcock_mode = True )

    session['dfe'] = n[1]
    # print( n )
    # print( n[0] )
    sock.emit( 'neighbors', render_template( "homies.html", homies = n[0] ) )

@sock.on('msg-send')
def msg_send(data):
    if 'uid' not in session:
        abort(Response("Permission denied, you have to login first"))
    obj = api.Messenger(session['uid'])
    tpuid = data['tpuid']

    data['id'] = f"{time.time()}".replace(".", "")
    data['date-sent'] = time.ctime(  )

    demo = "%s..." % " ".join(data['msg'].split(" ")[:5]) if len(data['msg']) > 15 else data['msg']
    res = obj.send_message( data['msg'], tpuid = data['tpuid'], _id = data['id'], 
    date_sent = data['date-sent'] )
    
    if (res == True):

        send = render_template( "send.html", msg = data, uid = data['tpuid'] )

        recv = render_template( "recv.html", uid = session['uid'], msg = data)

        send_filtered = render_template( "send_filtered.html", msg = data, uid = data['tpuid'] )

        recv_filtered = render_template( "recv_filtered.html", uid = session['uid'], msg = data)

        # room_ = str( api.FriendRequest.fetch_id(session['uid'], data['tpuid']) )
        room = str( data['r_id'] )
        # print( room, room_ )

        data = {'send': send, 'recv': recv,
            'send_filtered': send_filtered,
            'recv_filtered': recv_filtered, 'uid': session['uid']}

        emit( "msg-send", data, room = room )
        # print( f"\n\n{r_id}\n\n" )
        
        emit ('msg-notify', {
            'title': f"{session['name']} just sent you a message",
            'msg': demo,
            'uid': session['uid'],
            'tpuid': tpuid
            }, broadcast = True)

@sock.on('sending')
def on_sending(data):
    if 'uid' not in session:
        abort(Response('Permission denied. Login first'))
    room = data['room']
    emit( 'sending', str(session['uid']), room = room )

@sock.on( 'stopped-sending' )
def on_stopped_sending(data):
    room = data['room']
    emit('stopped-sending', str( session['uid'] ), room = room )

@sock.on( 'msg-see' )
def msg_see(data):
    res = api.Messenger(session['uid']).see( data['tpuid'] )
    if ( res ):
        emit( "msg-seen", {'uid': session['uid']}, room = data['room'] )

@sock.on('join')
def join_room_( data ):
    join_room( data )

@sock.on('leave')
def leave_room_( data ):
    try:
        leave_room( data )
    except:
        pass



@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')


@app.route('/offline.html')
def offline():
    return app.send_static_file('offline.html')


if __name__ == "__main__":
    sock.run( app, debug = True, host = '0.0.0.0' )