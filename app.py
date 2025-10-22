import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, BooleanField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

# --- Configuração ---
app = Flask(__name__)
# Chave secreta para segurança dos formulários (CSRF)
# Em produção, mude isso para algo aleatório e secreto
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil-de-adivinhar'

# Configuração do Banco de Dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'petshop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialização das Extensões ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Modelo do Banco de Dados ---
class Cachorro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(1), nullable=False) # 'M' ou 'F'
    proprietario = db.Column(db.String(100), nullable=False)
    
    # Campos adicionais
    classificacao = db.Column(db.String(50), default='')
    castrado = db.Column(db.Boolean, default=False)
    grau_energia = db.Column(db.String(1), nullable=False) # 'B', 'M', 'A'
    reativo_caes = db.Column(db.Boolean, default=False)
    reativo_pessoas = db.Column(db.Boolean, default=False)
    restricao_alimentos = db.Column(db.Text, default='')
    gosta_contato = db.Column(db.Boolean, default=True)
    responde_estimulos = db.Column(db.Boolean, default=True)

    frequencia_semanal = db.Column(db.Integer, default=1)
    passeia_na_praca = db.Column(db.Boolean, default=False)
    duracao_passeio = db.Column(db.Integer, default=30)
    grupo_passeio = db.Column(db.String(50), default='')
    enriquecimento_ambiental = db.Column(db.Boolean, default=False)
    atividade_mental = db.Column(db.Boolean, default=False)
    presencas = db.Column(db.Text, default='') # Pode ser melhorado no futuro

    def __repr__(self):
        return f'<Cachorro {self.nome}>'

# --- Formulário ---
class CachorroForm(FlaskForm):
    # Opções
    GENERO_CHOICES = [('M', 'Macho'), ('F', 'Fêmea')]
    ENERGIA_CHOICES = [('B', 'Baixo'), ('M', 'Médio'), ('A', 'Alto')]

    # Informações básicas
    nome = StringField('Nome', validators=[DataRequired()])
    data_nascimento = DateField('Data de Nascimento (AAAA-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    genero = SelectField('Gênero', choices=GENERO_CHOICES, validators=[DataRequired()])
    proprietario = StringField('Proprietário', validators=[DataRequired()])
    
    # Características e comportamento
    classificacao = StringField('Classificação (Ex: Porte, Raça)')
    castrado = BooleanField('Castrado')
    grau_energia = SelectField('Grau de Energia', choices=ENERGIA_CHOICES, validators=[DataRequired()])
    reativo_caes = BooleanField('Reativo a cães')
    reativo_pessoas = BooleanField('Reativo a pessoas')
    restricao_alimentos = TextAreaField('Restrição de Alimentos')
    gosta_contato = BooleanField('Gosta de contato físico')
    responde_estimulos = BooleanField('Responde a estímulos (brinquedos, etc)')

    # Informações de atividades
    frequencia_semanal = IntegerField('Frequência Semanal (visitas)', default=1, validators=[DataRequired(), NumberRange(min=0)])
    passeia_na_praca = BooleanField('Passeia na praça')
    duracao_passeio = IntegerField('Duração do Passeio (minutos)', default=30, validators=[DataRequired(), NumberRange(min=0)])
    grupo_passeio = StringField('Grupo do Passeio')
    enriquecimento_ambiental = BooleanField('Faz enriquecimento ambiental')
    atividade_mental = BooleanField('Faz atividade mental')
    presencas = TextAreaField('Registro de Presenças (Ex: 20/10, 22/10...)')
    
    submit = SubmitField('Salvar')

# --- Rotas (Views) ---

@app.route('/')
def index():
    """ Rota principal: Lista todos os cachorros. (READ) """
    cachorros = Cachorro.query.all()
    return render_template('index.html', cachorros=cachorros)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    """ Rota para Adicionar um novo cachorro. (CREATE) """
    form = CachorroForm()
    if form.validate_on_submit():
        # Coleta dados do formulário e cria um novo objeto Cachorro
        novo_cachorro = Cachorro(
            nome=form.nome.data,
            data_nascimento=form.data_nascimento.data,
            genero=form.genero.data,
            proprietario=form.proprietario.data,
            classificacao=form.classificacao.data,
            castrado=form.castrado.data,
            grau_energia=form.grau_energia.data,
            reativo_caes=form.reativo_caes.data,
            reativo_pessoas=form.reativo_pessoas.data,
            restricao_alimentos=form.restricao_alimentos.data,
            gosta_contato=form.gosta_contato.data,
            responde_estimulos=form.responde_estimulos.data,
            frequencia_semanal=form.frequencia_semanal.data,
            passeia_na_praca=form.passeia_na_praca.data,
            duracao_passeio=form.duracao_passeio.data,
            grupo_passeio=form.grupo_passeio.data,
            enriquecimento_ambiental=form.enriquecimento_ambiental.data,
            atividade_mental=form.atividade_mental.data,
            presencas=form.presencas.data
        )
        # Salva no banco de dados
        db.session.add(novo_cachorro)
        db.session.commit()
        flash('Cachorro cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))
    # Se for GET ou o formulário for inválido, mostra a página do formulário
    return render_template('form_cachorro.html', form=form, titulo='Adicionar Cachorro')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """ Rota para Editar um cachorro existente. (UPDATE) """
    cachorro = Cachorro.query.get_or_404(id)
    form = CachorroForm(obj=cachorro) # Pré-popula o formulário com os dados do cachorro

    if form.validate_on_submit():
        # Atualiza o objeto 'cachorro' com os dados do formulário
        cachorro.nome = form.nome.data
        cachorro.data_nascimento = form.data_nascimento.data
        cachorro.genero = form.genero.data
        cachorro.proprietario = form.proprietario.data
        cachorro.classificacao = form.classificacao.data
        cachorro.castrado = form.castrado.data
        cachorro.grau_energia = form.grau_energia.data
        cachorro.reativo_caes = form.reativo_caes.data
        cachorro.reativo_pessoas = form.reativo_pessoas.data
        cachorro.restricao_alimentos = form.restricao_alimentos.data
        cachorro.gosta_contato = form.gosta_contato.data
        cachorro.responde_estimulos = form.responde_estimulos.data
        cachorro.frequencia_semanal = form.frequencia_semanal.data
        cachorro.passeia_na_praca = form.passeia_na_praca.data
        cachorro.duracao_passeio = form.duracao_passeio.data
        cachorro.grupo_passeio = form.grupo_passeio.data
        cachorro.enriquecimento_ambiental = form.enriquecimento_ambiental.data
        cachorro.atividade_mental = form.atividade_mental.data
        cachorro.presencas = form.presencas.data
        
        # Salva as alterações no banco
        db.session.commit()
        flash('Dados do cachorro atualizados com sucesso!', 'success')
        return redirect(url_for('index'))
    
    # Se for um request GET, mostra o formulário pré-populado
    return render_template('form_cachorro.html', form=form, titulo='Editar Cachorro')

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    """ Rota para Deletar um cachorro. (DELETE) """
    cachorro = Cachorro.query.get_or_404(id)
    db.session.delete(cachorro)
    db.session.commit()
    flash('Cachorro removido com sucesso.', 'info')
    return redirect(url_for('index'))

# Permite rodar o app com "python app.py"
if __name__ == '__main__':
    app.run(debug=True)
