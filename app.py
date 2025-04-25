from flask import Flask, render_template, request, redirect, session, url_for
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta'

usuarios = {}
cursos = []
matriculas = []

@app.route('/')
def home():
    if 'usuario' in session:
        tipo = session.get('tipo')
        if tipo == 'professor':
            return render_template('professor_home.html', usuario=session['usuario'])
        elif tipo == 'aluno':
            aluno = session['usuario']
            cursos_aluno = [m['curso'] for m in matriculas if m['aluno'] == aluno]
            cursos_disponiveis = [c for c in cursos if c['nome'] in cursos_aluno]
            return render_template('home_aluno.html', usuario=aluno, cursos=cursos_disponiveis)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        if nome in usuarios and usuarios[nome]['senha'] == senha:
            session['usuario'] = nome
            session['tipo'] = usuarios[nome]['tipo']
            return redirect('/')
        return 'Usuário ou senha incorretos'
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        tipo = request.form['tipo']
        usuarios[nome] = {'senha': senha, 'tipo': tipo}
        return redirect('/login')
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/cadastrar_curso', methods=['GET', 'POST'])
def cadastrar_curso():
    if 'usuario' in session and session.get('tipo') == 'professor':
        if request.method == 'POST':
            arquivo = request.files['arquivo']
            filename = ""
            if arquivo:
                filename = arquivo.filename
                caminho_arquivo = os.path.join('static', filename)
                os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
                arquivo.save(caminho_arquivo)
            curso = {
                'nome': request.form['nome'],
                'carga_horaria': request.form['carga_horaria'],
                'tipo': request.form['tipo'],
                'arquivo': filename
            }
            cursos.append(curso)
            return redirect('/')
        return render_template('cadastrar_curso.html')
    return redirect('/')

@app.route('/matricular', methods=['GET', 'POST'])
def matricular():
    if 'usuario' in session and session.get('tipo') == 'professor':
        if request.method == 'POST':
            aluno = request.form['aluno']
            curso = request.form['curso']
            if not any(m['aluno'] == aluno and m['curso'] == curso for m in matriculas):
                matriculas.append({'aluno': aluno, 'curso': curso})
            return redirect('/matricular')
        alunos = [k for k, v in usuarios.items() if v['tipo'] == 'aluno']
        return render_template('matricular.html', alunos=alunos, cursos=cursos)
    return redirect('/')

@app.route('/ver_material/<nome>')
def ver_material(nome):
    if 'usuario' in session and session.get('tipo') == 'aluno':
        for curso in cursos:
            if curso['nome'] == nome:
                session['start_time'] = datetime.now().isoformat()
                session['curso_visualizado'] = nome
                return render_template('ver_material.html', curso=curso)
    return redirect('/')

@app.route('/concluir/<nome>', methods=['POST'])
def concluir(nome):
    if 'usuario' in session and session.get('tipo') == 'aluno':
        aluno = session['usuario']
        end_time = datetime.now()
        start_time = session.pop('start_time', None)
        curso_visualizado = session.pop('curso_visualizado', None)
        if start_time and curso_visualizado:
            start_dt = datetime.fromisoformat(start_time)
            tempo_total = (end_time - start_dt).total_seconds() / 60
            for curso in cursos:
                if curso['nome'] == nome:
                    curso.setdefault('progresso', {})[aluno] = {
                        'tempo': round(tempo_total, 2),
                        'concluido': True
                    }
                    return render_template('certificado.html', aluno=aluno, curso=curso['nome'], carga=curso['carga_horaria'])
    return redirect('/')

@app.route('/acompanhamento')
def acompanhamento():
    if 'usuario' in session and session.get('tipo') == 'professor':
        return render_template('acompanhamento.html', cursos=cursos, matriculas=matriculas)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
