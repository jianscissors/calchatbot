const $ = (id) => document.getElementById(id);

function addMessage(text, cls = 'bot'){
  const d = document.createElement('div');
  d.className = `msg ${cls}`;
  d.textContent = text;
  $('messages').appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}

async function sendMessage(){
  const t = $('message').value.trim();
  if(!t) return;
  addMessage(t, 'user');
  $('message').value = '';
  try{
    const res = await fetch('/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message:t})
    });
    const json = await res.json();
    addMessage(json.reply || '(no reply)', 'bot');
  }catch(err){
    addMessage('Error: ' + err.message, 'bot');
  }
}

$('send').addEventListener('click', sendMessage);
$('message').addEventListener('keydown', (e)=>{
    if(e.key==='Enter' && !e.shiftKey){ 
        e.preventDefault(); 
        sendMessage(); 
    } 
});
