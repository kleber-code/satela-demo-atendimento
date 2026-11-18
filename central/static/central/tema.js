(function(){
  var raiz=document.documentElement;
  function atual(){var t=raiz.dataset.tema;if(t)return t;return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro'}
  document.querySelectorAll('[data-alternar-tema]').forEach(function(b){
    b.addEventListener('click',function(){
      var n=atual()==='escuro'?'claro':'escuro';
      raiz.dataset.tema=n;
      try{localStorage.setItem('tema',n)}catch(e){}
    });
  });
})();
