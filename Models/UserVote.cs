using Microsoft.AspNetCore.Identity;
using System.ComponentModel.DataAnnotations;

namespace EksiCaciklar.Models
{
    public class UserVote
    {
        public int Id { get; set; }
        public int MovieId { get; set; }
        public Movie Movie { get; set; } = default!;
        public string UserId { get; set; } = default!;
        public IdentityUser User { get; set; } = default!;

        // ARTIK TEK PUAN DEĞİL, 5 DETAY PUAN TUTUYORUZ
        [Range(0, 100)] public int ScoreScenario { get; set; }
        [Range(0, 100)] public int ScoreActing { get; set; }
        [Range(0, 100)] public int ScoreVisuals { get; set; }
        [Range(0, 100)] public int ScoreSound { get; set; }
        [Range(0, 100)] public int ScoreEditing { get; set; }

        public string? Comment { get; set; }
    }
}