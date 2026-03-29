namespace EksiCaciklar.Models
{
    public class UserViewModel
    {
        public string UserId { get; set; } = string.Empty;
        public string UserName { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public bool IsAdmin { get; set; } // Bu kişi yönetici mi?
    }
}