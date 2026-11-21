"""Cine Leandro v2 — Arquitetura Limpa.

cinema/
├── entidades/          ⚪ Entities: regras do negócio (Python puro)
├── casos_de_uso/       🟡 Use Cases + portas (interfaces) + DTOs
├── adaptadores/        🔵 Controllers (DRF), Presenters, Repositórios (ORM), Gateways (TMDB), Segurança, E-mail
└── frameworks_drivers/ 🟠 Django, configuração e o container que liga tudo
"""
