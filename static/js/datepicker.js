class Picker {
    constructor($elm) {
        this.$elm = $elm;
        this.$input = this.$elm.find(".input");
        this.$display = this.$elm.find(".display");

        this.$input.css({
          fontSize: /iphone|ipad|ipod|android/.test(navigator.userAgent.toLowerCase()) ? "16px" : "9999px"
        }).val(this._getDate()).on("change", (evt) => {
            this._display();
        }).trigger("change");
         
        this._setInputSize();
    }
    
    _setInputSize() {
        this.$input.width(this.$elm.width());
        this.$input.height(this.$elm.height());
    }

    _getDate() {
      var now = new Date();

      return (now.getFullYear()) + "-" + ("0" + (now.getMonth() + 1)).slice(-2) + "-" + ("0" + now.getDate()).slice(-2);
    }
  
    _display() {
      if (this.$input.val()) {
        this.$display.html("<p class='year'>" + (this.$input.val()).replace("-", "</p><p class='month'>").replace("-", "</p><p class='day'>").replace(/^\d\d/, "") + "</p>");
      } else {
        this.$display.html("<p class='year'></p><p class='month'></p><p class='day'></p>");
      }
    }
}
