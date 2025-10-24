import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, DateField, SelectField, BooleanField, TextAreaField, SubmitField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, Optional
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do .env

# --- Configuração ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-dificil-de-adivinhar')
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuração do Banco de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'petshop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração de Upload
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

# --- Inicialização das Extensões ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Modelos do Banco de Dados ---
class Cachorro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(1), nullable=False) # 'M' ou 'F'
    proprietario = db.Column(db.String(100), nullable=False)
    
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
    presencas = db.Column(db.Text, default='')
    
    # Novo campo de foto
    foto_perfil = db.Column(db.String(100), nullable=False, default='default_pet.png')

    def __repr__(self):
        return f'<Cachorro {self.nome}>'

# --- Formulários ---
def save_picture(form_picture):
    # Gera um nome aleatório para o arquivo
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Salva a imagem
    form_picture.save(picture_path)
    
    return picture_fn

class CachorroForm(FlaskForm):
    nome = StringField('Nome do pet', validators=[DataRequired(), Length(min=2, max=100)])
    data_nascimento = DateField('Data de Nascimento (AAAA-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    genero = SelectField('Gênero', choices=[('M', 'Macho'), ('F', 'Fêmea')], validators=[DataRequired()])
    proprietario = StringField('Nome do dono', validators=[DataRequired(), Length(min=2, max=100)])
    classificacao = StringField('Classificação (Ex: Porte Pequeno, Raça)', validators=[Optional(), Length(max=50)])
    castrado = BooleanField('Castrado')
    grau_energia = SelectField('Grau de Energia', choices=[('B', 'Baixo'), ('M', 'Médio'), ('A', 'Alto')], validators=[DataRequired()])
    reativo_caes = BooleanField('Reativo a cães')
    reativo_pessoas = BooleanField('Reativo a pessoas')
    restricao_alimentos = TextAreaField('Restrição de Alimentos (Opcional)')
    gosta_contato = BooleanField('Gosta de contato físico')
    responde_estimulos = BooleanField('Responde a estímulos (brinquedos, etc)')
    frequencia_semanal = IntegerField('Frequência Semanal (visitas)', default=1, validators=[DataRequired()])
    passeia_na_praca = BooleanField('Passeia na praça')
    duracao_passeio = IntegerField('Duração do Passeio (minutos)', default=30, validators=[DataRequired()])
    grupo_passeio = StringField('Grupo do Passeio', validators=[Optional(), Length(max=50)])
    enriquecimento_ambiental = BooleanField('Faz enriquecimento ambiental')
    atividade_mental = BooleanField('Faz atividade mental')
    presencas = TextAreaField('Registro de Presenças (Ex: 20/10, 22/10...)')
    foto = FileField('Foto do Pet (Opcional, max 5MB)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens .jpg ou .png são permitidas!'),
        FileSize(max_size=app.config['MAX_CONTENT_LENGTH'], message='A foto deve ter no máximo 5MB.')
    ])
    submit = SubmitField('Salvar')

# --- Rotas (Views) ---

@app.route('/')
def index():
    # --- LÓGICA DE PAGINAÇÃO E PESQUISA ---
    PER_PAGE = 10 # Define quantos pets por página
    
    query = request.args.get('pesquisa')
    page = request.args.get('page', 1, type=int) # Pega o nº da página da URL
    
    # Começa a construir a busca
    base_query = Cachorro.query
    
    if query:
        # Se houver uma pesquisa, filtra por nome do pet OU nome do proprietário
        search_term = f"%{query}%"
        base_query = base_query.filter(
            db.or_(
                Cachorro.nome.ilike(search_term),
                Cachorro.proprietario.ilike(search_term)
            )
        )
    
    # Ordena alfabeticamente e aplica a paginação
    pagination = base_query.order_by(Cachorro.nome.asc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    # --- FIM DA LÓGICA ---
    
    return render_template('index.html', pagination=pagination, query=query)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    form = CachorroForm()
    if form.validate_on_submit():
        # Salva a foto, se ela existir
        foto_filename = 'default_pet.png' # Padrão
        if form.foto.data:
            foto_filename = save_picture(form.foto.data)

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
            presencas=form.presencas.data,
            foto_perfil=foto_filename # Salva o nome do arquivo da foto
        )
        db.session.add(novo_cachorro)
        db.session.commit()
        flash('Cachorro cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('form_cachorro.html', form=form, titulo='Adicionar Cachorro')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    cachorro = Cachorro.query.get_or_404(id)
    form = CachorroForm(obj=cachorro) # Preenche o form com dados existentes
    
    if form.validate_on_submit():
        # Lógica de atualização
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
        
        # Lógica para atualizar a foto
        if form.foto.data:
            # Deleta a foto antiga, se não for a default
            if cachorro.foto_perfil != 'default_pet.png':
                old_foto_path = os.path.join(app.config['UPLOAD_FOLDER'], cachorro.foto_perfil)
                if os.path.exists(old_foto_path):
                    os.remove(old_foto_path)
            # Salva a nova foto
            cachorro.foto_perfil = save_picture(form.foto.data)

        db.session.commit()
        flash('Dados do cachorro atualizados!', 'success')
        return redirect(url_for('index'))
    
    # Passa o objeto 'cachorro' para o template
    return render_template('form_cachorro.html', form=form, titulo='Editar Cachorro', cachorro=cachorro)

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    cachorro = Cachorro.query.get_or_404(id)
    
    # Deleta a foto, se não for a default
    if cachorro.foto_perfil != 'default_pet.png':
        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], cachorro.foto_perfil)
        if os.path.exists(foto_path):
            os.remove(foto_path)
            
    db.session.delete(cachorro)
    db.session.commit()
    flash('Cachorro removido com sucesso.', 'info')
    return redirect(url_for('index'))

# Para rodar a aplicação
if __name__ == '__main__':
    app.run(debug=True)
