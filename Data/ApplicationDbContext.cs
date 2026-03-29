using EksiCaciklar.Models; // Modelinin olduğu yer
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace EksiCaciklar.Data // Namespace ismin proje isminle aynı olmalı
{
    // Partial ibaresini kaldırdık, tek patron bu sınıf.
    public class ApplicationDbContext : IdentityDbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        // "= default!;" diyerek "boş gelirse korkma" dedik (Null hatası çözümü)
        public DbSet<Movie> Movies { get; set; } = default!;

        // YENİ EKLENEN TABLO:
        public DbSet<UserVote> UserVotes { get; set; } = default!;
    }
}